import os
import re
import ast
import zipfile
import shutil
import tempfile
import httpx
import asyncio

from uuid import UUID

from datetime import datetime

from fastapi import HTTPException, BackgroundTasks

from .models import Scan
from .store import ScanStore
from .agent import ScanIntelligenceAgent

# CRYPTOGRAPHIC RULES/REGEXES FOR DETECTION AND CLASSIFICATION:
""" We are creating a specific compiled pattern (a specific "detector") for each cryptographic algorithm family.
re.compile() takes a string and produces a re.Pattern object. Instead of using the strings directly, creating a regex object. """

RULES = {
    # Future-Proof against Quantum Computers
    'POST_QUANTUM': {
        'ML-KEM/Kyber': re.compile(r'\b(kyber|ml-kem)\b', re.IGNORECASE),
        'ML-DSA/Dilithium': re.compile(r'\b(dilithium|ml-dsa)\b', re.IGNORECASE),
        'FN-DSA/Falcon': re.compile(r'\b(falcon|fn-dsa)\b', re.IGNORECASE),
        'SLH-DSA/SPHINCS+': re.compile(r'\b(sphincs|slh-dsa)\b', re.IGNORECASE),
    },

    """ 'r' - Raw String (protects backslashes)
    '\b' - Word Boundary (start and end)
    '|' - OR
    're.IGNORECASE' - Ignore-Case Flag """

    # Will be cracked when Quantum Computers arrive
    'QUANTUM_VULNERABLE': {
        'RSA': re.compile(r'\b(rsa|pkcs1|pkcs8|rsassa)\b', re.IGNORECASE),
        'ECDSA': re.compile(r'\b(ecdsa|secp256k1|nistp256|nistp384|prime256v1)\b', re.IGNORECASE),
        'ECDH/DH': re.compile(r'\b(ecdh|diffie-hellman|x25519|curve25519)\b', re.IGNORECASE),
        'EdDSA/Ed25519': re.compile(r'\b(ed25519|eddsa|ed448)\b', re.IGNORECASE),
    },

    # Strong Classical Symmetric Encryption
    'QUANTUM_SAFE_CLASSICAL': {
        'AES-256': re.compile(r'\b(aes[-_]?256|aes|rijndael)\b', re.IGNORECASE),
        'ChaCha20': re.compile(r'\b(chacha20|poly1305)\b', re.IGNORECASE),
        'SHA-256/SHA-512': re.compile(r'\b(sha256|sha-256|sha512|sha-512)\b', re.IGNORECASE),
        'SHA-3': re.compile(r'\b(sha3|keccak)\b', re.IGNORECASE),
    },
 
    # Already broken TODAY even by regular computers
    'CLASSICAL_VULNERABLE': {
        'MD5': re.compile(r'\b(md5)\b', re.IGNORECASE),
        'SHA-1': re.compile(r'\b(sha1|sha-1)\b', re.IGNORECASE),
        'DES/3DES': re.compile(r'\b(des|3des|triple[-_]?des)\b', re.IGNORECASE),
        'RC4': re.compile(r'\b(rc4|arc4)\b', re.IGNORECASE),
    }
}

# DYNAMIC TREE-SITTER LOADING CONFIG.:
""" Tree Sitter is a special case; it's not a pure Python package; it uses C/C++.
Libraries like fastapi, pydantic, and httpx are written in standard Python, and they install smoothly on any computer in seconds.
But Tree Sitter, since is C/C++, it often requires a C++ Compiler.
If a developer doesn't have C++ build tools installed, Tree Sitter will fail to install and crash the program.
We don't want that. """

HAS_TREE_SITTER = False

try:
    from tree_sitter import Language, Parser

    import tree_sitter_go as tsgo
    import tree_sitter_javascript as tsjs
    import tree_sitter_java as tsjava

    GO_LANG = Language(tsgo.language())
    JS_LANG = Language(tsjs.language())
    JAVA_LANG = Language(tsjava.language())

    HAS_TREE_SITTER = True

except Exception:
    pass

class PythonCryptoVisitor(ast.NodeVisitor):
    """ ast.NodeVisitor is used so our scanner understands Python grammar,
    allowing it to inspect only real executable function calls and imports while completely ignoring comments and text noise. """

    def __init__(self, file_path: str, lines: list[str]):
        self.file_path = file_path
        self.lines = lines

        self.findings = []

        # We have to look for the Python packages that we use to import the algorithms from.
        self.crypto_libs = {'cryptography', 'pycryptodome', 'Crypto', 'hashlib', 'ssl'}

    # Visit the 'import ...' nodes
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] in self.crypto_libs:
                self._add_finding(node.lineno, 'Library Import', 'General', f'Imported cryptographic library: {alias.name}')

        # Keep walking down the tree
        self.generic_visit(node)

    # Visit the 'from ... import ...' nodes
    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] in self.crypto_libs:
            for alias in node.names:
                self._add_finding(node.lineno, 'Library Import', 'General', f'Imported {alias.name} from {node.module}')

        self.generic_visit(node)

    # Visit the function call nodes
    def visit_Call(self, node):
        func_name = ''

        # Method / Dotted call:
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr # An ast.Attribute instance has an '.attr' property.

        # Direct function call:
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id # An ast.Name instance has an '.id. property.

        # Scan function name using our RULES
        for category, algs in RULES.items():
            for alg_name, pattern in algs.items():
                if pattern.findall(func_name):
                    self._add_finding(node.lineno, category, alg_name, f'Called function: {func_name}')

        self.generic_visit(node)

    # Visit the string nodes
    def visit_Constant(self, node):
        # Match string literals (e.g. cipher = Cipher(algorithms.AES(key), mode='AES-256'); catches 'AES-256')

        if isinstance(node.value, str):
            val = node.value

            for category, algs in RULES.items():
                for alg_name, pattern in algs.items():
                    if pattern.findall(val):
                        self._add_finding(node.lineno, category, alg_name, f"Constant string: '{val}'")

    def _add_finding(self, line_number: int, category: str, algorithm: str, detail: str):
        line_content = self.lines[line_number - 1].strip() if line_number <= len(self.lines) else ''

        self.findings.append({
            'file': self.file_path,
            'line_number': line_number,
            'category': category,
            'algorithm': algorithm,
            'line_content': line_content[:150]
        })


class ScanService:
    def __init__(self, scan_store: ScanStore):
        self.scan_store = scan_store
        self.scannable_extensions = {
            '.py', '.js', '.ts', '.go', '.java', '.cpp', '.c', 
            '.rs', '.cs', '.php', '.rb', '.swift', '.kt', '.h'
        }

        self.ignored_dirs = {
            'node_modules', 'venv', '.venv', 'env', '.git', 
            '__pycache__', 'dist', 'build', '.github'
        }

    # API CORE METHODS
    async def get_scan(self, user_id: UUID, scan_id: UUID) -> Scan:
        scan = await self.scan_store.get_by_id(scan_id, user_id)

        if not scan:
            raise HTTPException(
                status_code=404,
                detail='Scan not found'
            )

        return scan

    async def list_scans(self, user_id: UUID, repository_id: UUID) -> list[Scan]:
        return await self.scan_store.list_by_repository(repository_id, user_id)

    # 2. Authenticate the user and repository and assign tasks in the background -> run_scan_job
    async def trigger_scan(
        self, 
        user_id: UUID, 
        repository_id: UUID, 
        repo_full_name: str, 
        token: str | None, 
        background_tasks: BackgroundTasks
    ) -> Scan:
        scan = await self.scan_store.create(repository_id, user_id)

        background_tasks.add_task(
            self.run_scan_job, 
            scan.id, 
            repo_full_name, 
            token
        )

        """ add_task does not run the function immediately, instead it just saves the function and the arguments for later in background tasks.
        That is why we provide the function and the arguments separate in add_task. """

        return scan

    # JOB ORCHESTRATOR
    # 3. Execute the scan -> scan_directory
    async def run_scan_job(self, scan_id: UUID, full_name: str, token: str | None = None):
        # Update status from 'pending' to 'running'
        await self.scan_store.update_status(scan_id, 'running')

        zip_path = None
        temp_dir = None

        try:
            # Download zip archive from GitHub
            zip_path = await self.download_github_zip(full_name, token)

            # Create a temporary folder and extract the zip into it:
            temp_dir = tempfile.mkdtemp()

            self.extract_zip(zip_path, temp_dir)

            # Perform the scan
            findings_data = self.scan_directory(temp_dir)

            # AI INTELLIGENCE AGENT ENRICHMENT
            if findings_data:
                agent = ScanIntelligenceAgent()
                semaphore = asyncio.Semaphore(3)  # Limits concurrent Ollama requests to 3

                async def process_finding(finding: dict):
                    async with semaphore:
                        # Extract the code context around the matched line
                        context = self._get_code_context(
                            temp_dir=temp_dir, 
                            file_path=finding['file'], 
                            line_number=finding['line_number']
                        )

                        # Ask Ollama to audit it
                        audit = await agent.analyze_finding(
                            file_path=finding['file'],
                            line_number=finding['line_number'],
                            category=finding['category'],
                            algorithm=finding['algorithm'],
                            matched_line=finding['line_content'],
                            code_context=context
                        )

                        # Enrich the finding dict
                        finding['is_false_positive'] = audit.is_false_positive
                        finding['agent_explanation'] = audit.agent_explanation
                        finding['suggested_explanation'] = audit.suggested_explanation

                # Run AI analysis for all findings concurrently (gated by semaphore)
                await asyncio.gather(*(process_finding(f) for f in findings_data))

            await self.scan_store.save_findings(scan_id, findings_data)
            await self.scan_store.update_status(
                scan_id, 
                'completed', 
                completed_at=datetime.now()
            )

        except Exception as e:
            await self.scan_store.update_status(scan_id, 'failed')

            print(f'Scan {scan_id} failed: {str(e)}')

        finally:
            # Always delete the zip file and scratchpad folder!

            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)

            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    # AST AND PARSING ENGINES
    # 4. The Smart Folder Walker (os.walk) -> scan_python_ast/scan_tree_sitter/scan_content_regex
    def scan_directory(self, dir_path: str) -> list[dict]:
        results = []

        for root, dirs, files in os.walk(dir_path):
            """ os.walk(dir_path) is a built-in Python generator. It crawls through every single child-grandchild folder and files.
            As it crawls through your folders, for every single directory it visits,
            it yields a 3-item tuple: (root, dirs, files).

            root (string) - The path of the folder you are currently standing in
            dirs (list of strings) - All sub-folders inside root
            files (list of strings) - All files inside root """

            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

            """ Notice '[:]' in 'dirs[:]'? It's called Slice Assignment (in-place replacement).
            If we were to write 'dirs = ...', we will be creating a new variable.
            But by using this notation, we are modifying the existing list object in-place. """

            for file in files:
                # Get file extension
                file_ext = os.path.splitext(file)[1].lower()

                """ splitext is built by Python specifically to always find the real file extension.
                eg: 'login.py' -> ('login', '.py') """

                if file_ext in self.scannable_extensions:
                    # Get the full absolute path to open the file
                    full_file_path = os.path.join(root, file) # 1. Give to open() to read the file from the disk

                    """ root = 'C:\temp\scan_123\alice-crypto-app-9a7b\src\auth'
                    file = 'login.py'
                    full_file_path = 'C:\temp\scan_123\alice-crypto-app-9a7b\src\auth\login.py' """

                    """ Why not just write root + '/' + file?
                    Windows uses backslashes (\) and Linux uses forward slashes (/).
                    If you use + '/', on Windows your path becomes C:\temp/src/auth\login.py (mixed slashes that can cause crashes).
                    os.path.join automatically uses the right slash on any computer. """

                    # Calculate relative path
                    rel_path = os.path.relpath(full_file_path, dir_path) # Remove the ugly temp folder path

                    # Clean up the path for the dashboard
                    parts = rel_path.split(os.sep)

                    # os.sep stands for 'Operating System Seperator', which dynamically gives you either '/' or '\' according to the OS.

                    display_path = os.path.join(*parts[1:]) if len(parts) > 1 else rel_path # 2. Saved in database and shown on the screen

                    try:
                        with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                            # Traffic Controller
                            if file_ext == '.py':
                                results.extend(self.scan_python_ast(content, display_path))

                            elif file_ext == '.go' and HAS_TREE_SITTER:
                                results.extend(self.scan_tree_sitter(content, display_path, GO_LANG))

                            elif file_ext in ('.js', '.ts') and HAS_TREE_SITTER:
                                results.extend(self.scan_tree_sitter(content, display_path, JS_LANG))

                            elif file_ext == '.java' and HAS_TREE_SITTER:
                                results.extend(self.scan_tree_sitter(content, display_path, JAVA_LANG))

                            else:
                                results.extend(self.scan_content_regex(content, display_path))

                    except Exception:
                        pass
        return results

    # 5 a. Analyze Python files via Abstract Syntax Tree (AST) inspection
    def scan_python_ast(self, content: str, file_path: str) -> list[dict]:
        try:
            # Turn Python text into AST
            tree = ast.parse(content)

            # Instantiate the node visitor
            visitor = PythonCryptoVisitor(file_path, content.splitlines())

            # Walk through all nodes (imports, function calls, constants)
            visitor.visit(tree)

            # Return all collected vulnerabilities
            return visitor.findings

        except Exception:
            # If the file has a Python syntax error, safely fall back to regex
            return self.scan_content_regex(content, file_path)

    # 5 b. Analyze Tree-Sitter supported languages (JS/TS/Go/Java) using syntax trees
    def scan_tree_sitter(self, content: str, file_path: str, language: Language) -> list[dict]:
        findings = []

        # Initialize Tree-Sitter for the specific language
        parser = Parser(language)
        tree = parser.parse(bytes(content, 'utf8'))

        # Walk through every node in the syntax tree (Depth-First Search)
        nodes_to_visit = [tree.root_node]

        while nodes_to_visit:
            node = nodes_to_visit.pop()

            # Ignore comments
            if 'comment' in node.type:
                continue

            # Scan text content in leaf nodes (identifiers, strings, function names)
            if not node.children:
                try:
                    node_text = content[node.start_byte:node.end_byte]

                    if node_text:
                        for category, algs in RULES.items():
                            for alg_name, pattern in algs.items():
                                if pattern.findall(node_text):
                                    line_num = node.start_point[0] + 1
                                    lines = content.splitlines()
                                    line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ''

                                    findings.append({
                                        'file': file_path,
                                        'line_number': line_num,
                                        'category': category,
                                        'algorithm': alg_name,
                                        'line_content': line_content[:150]
                                    })
                except Exception:
                    pass

            nodes_to_visit.extend(node.children)

        return findings

    # 5 c. Fallback regex scanner for all other programming languages
    def scan_content_regex(self, content: str, file_path: str) -> list[dict]:
        findings = []
        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for category, algs in RULES.items():
                for alg_name, pattern in algs.items():
                    if pattern.findall(line):
                        findings.append({
                            'file': file_path,
                            'line_number': line_num,
                            'category': category,
                            'algorithm': alg_name,
                            'line_content': line.strip()[:150]
                        })
        return findings

    # ZIPBALL DOWNLOADS
    async def download_github_zip(self, full_name: str, token: str | None = None) -> str:
        url = f'https://api.github.com/repos/{full_name}/zipball'

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Transit-App'
        }

        if token:
            headers['authorization'] = f'token {token}'

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Ask GitHub for the zip bytes over HTTP
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                raise Exception(f'Failed to download repository zipball: {response.text}')

            # Create an empty file on the hard drive
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

            # Pour GitHub's zip bytes into that file
            temp_file.write(response.content)
            temp_file.close()

            """ 'Downloading a file' in Python means asking GitHub for the .zip bytes over the internet,
            creating an empty file on disk with NamedTemporaryFile(), and saving those bytes into it. """

            # Return the path of that saved zip file
            return temp_file.name

    def extract_zip(self, zip_path: str, extract_to: str):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    # HELPER
    # Extract surrounding code lines for AI context (20-line window).
    def _get_code_context(self, temp_dir: str, file_path: str, line_number: int, range_lines: int = 10) -> str:
        try:
            # Locate and open the file:
            dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]

            if not dirs:
                return ''

            full_path = os.path.join(temp_dir, dirs[0], file_path)

            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Fetch 10 lines before and after the matched line
            start = max(0, line_number - 1 - range_lines)
            end = min(len(lines), line_number + range_lines)

            # Return the combined 20 lines of code as string
            return ''.join(lines[start:end])

        except Exception:
            return ''
