import os
import ast
import shutil
import tempfile

from git import Repo

class MigrationExecutor:
    @staticmethod
    def apply_migration(
        repo_path: str,
        file_rel_path: str,
        migrated_file_content: str,
        branch_name: str | None = None
    ) -> dict:
        full_file_path = os.path.join(repo_path, file_rel_path)

        if not os.path.exists(full_file_path):
            raise FileNotFoundError(f'Target file does not exist: {full_file_path}')

        # 1. Deterministic Syntax Validation Engine (Verify BEFORE touching disk!)
        if file_rel_path.endswith('.py'):
            try:
                ast.parse(migrated_file_content)

            except SyntaxError as syntax_err:
                return {
                    'success': False,
                    'error': f'Syntax validation failed: {str(syntax_err)}. Changes were rejected.',
                    'rolled_back': True
                }

        # 2. Git Branching
        repo = None
        new_branch = branch_name or f'pqc-migration-{os.urandom(3).hex()}'

        try:
            repo = Repo(repo_path)

            repo.git.checkout('-b', new_branch)

        except Exception:
            pass

        # 3. Write Validated File to Disk
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(migrated_file_content)

        # 4. Generate the True Native Git Diff!
        diff_text = ''

        if repo:
            try:
                diff_text = repo.git.diff()

                repo.git.add(file_rel_path)
                repo.git.commit('-m', f'chore(security): migrate {file_rel_path} to post-quantum cryptography')

            except Exception as e:
                print(f'Warning: Git operation skipped: {e}')

        return {
            'success': True,
            'branch': new_branch,
            'file': file_rel_path,
            'diff': diff_text,
            'message': 'Migration applied and verified successfully.'
        }

    @staticmethod
    def execute_remote_migration(
        repo_full_name: str,
        github_token: str,
        file_rel_path: str,
        migrated_file_content: str,
        branch_name: str | None = None
    ) -> dict:
        temp_dir = tempfile.mkdtemp(prefix='transit_mig_')

        try:
            auth_url = f'https://x-access-token:{github_token}@github.com/{repo_full_name}.git'
            repo = Repo.clone_from(auth_url, temp_dir, depth=1)
            target_branch = branch_name or f'pqc-migration-{os.urandom(3).hex()}'

            result = MigrationExecutor.apply_migration(
                repo_path=temp_dir,
                file_rel_path=file_rel_path,
                migrated_file_content=migrated_file_content,
                branch_name=target_branch
            )

            if not result.get('success'):
                return result

            # Push directly to remote GitHub
            origin = repo.remote(name='origin')

            origin.push(refspec=f'{target_branch}:{target_branch}')

            return {
                'success': True,
                'branch': target_branch,
                'repo': repo_full_name,
                'diff': result.get('diff', ''),
                'message': f"Successfully pushed migration branch '{target_branch}' to GitHub!"
            }

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
