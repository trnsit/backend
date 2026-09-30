import asyncio

from .vector_store import VectorStore

KNOWLEDGE_DOCUMENTS = [
    {
        'title': 'NIST FIPS 203: ML-KEM Standard for Key Encapsulation',
        'category': 'POST_QUANTUM',
        'source': 'NIST FIPS 203',
        'content': (
            'NIST FIPS 203 standardizes ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism, '
            'derived from CRYSTALS-Kyber). ML-KEM is the primary post-quantum standard for general encryption '
            'and key establishment. It replaces classical key exchange algorithms including RSA key exchange, '
            'Diffie-Hellman (DH), and Elliptic-Curve Diffie-Hellman (ECDH/X25519). '
            'Standard parameter sets include ML-KEM-512, ML-KEM-768 (recommended general security), and ML-KEM-1024.'
        )
    },
    {
        'title': 'NIST FIPS 204: ML-DSA Standard for Digital Signatures',
        'category': 'POST_QUANTUM',
        'source': 'NIST FIPS 204',
        'content': (
            'NIST FIPS 204 standardizes ML-DSA (Module-Lattice-Based Digital Signature Algorithm, '
            'derived from CRYSTALS-Dilithium). ML-DSA is the primary post-quantum standard for general-purpose '
            'digital signatures. It is designed to replace classical digital signatures such as RSA signing (PKCS#1, RSASSA), '
            'DSA, and ECDSA (secp256k1, prime256v1). Used for authentication, TLS certificates, and JWT token signing. '
            'Standard parameter sets are ML-DSA-44, ML-DSA-65 (recommended general use), and ML-DSA-87.'
        )
    },
    {
        'title': 'NIST FIPS 205: SLH-DSA Stateless Hash-Based Signatures',
        'category': 'POST_QUANTUM',
        'source': 'NIST FIPS 205',
        'content': (
            'NIST FIPS 205 standardizes SLH-DSA (Stateless Hash-Based Digital Signature Algorithm, '
            'derived from SPHINCS+). SLH-DSA provides digital signatures based solely on secure hash functions '
            '(SHA-2, SHAKE) rather than lattice math. It serves as an independent fallback if lattice cryptography '
            'develops vulnerabilities. It is ideal for high-assurance firmware signing, long-term archival signing, '
            'and applications where signature generation frequency is low.'
        )
    },
    {
        'title': 'Migration Guidance: Replacing RSA and ECDSA Signatures in JWT and Authentication',
        'category': 'MIGRATION_PLAYBOOK',
        'source': 'Transit Security Advisory',
        'content': (
            'To migrate RSA (RS256, RS384, RS512) or ECDSA (ES256, ES384) in authentication and JWT signing: '
            '1. Migrate to ML-DSA-65 (FIPS 204) for full post-quantum protection. '
            '2. For hybrid transitions, use a composite dual-signature scheme pairing Ed25519 with ML-DSA-65. '
            "3. Libraries: In Python, use liboqs via 'oqs-python' or PyCryptodome/cryptography with PQC plugins."
        )
    },
    {
        'title': 'Migration Guidance: Replacing Diffie-Hellman and ECDH Key Exchange',
        'category': 'MIGRATION_PLAYBOOK',
        'source': 'Transit Security Advisory',
        'content': (
            'Classical key agreement protocols (Diffie-Hellman, ECDH, X25519) are vulnerable to store-now-decrypt-later '
            "quantum attacks via Shor's algorithm. Applications should migrate key exchange mechanisms to ML-KEM-768 (FIPS 203). "
            'In TLS, deploy hybrid key exchange (such as X25519+ML-KEM-768) which is supported in modern OpenSSL 3.x and liboqs.'
        )
    },
    {
        'title': 'Deprecation Notice: MD5 and SHA-1 Vulnerabilities',
        'category': 'CLASSICAL_VULNERABLE',
        'source': 'NIST SP 800-131A',
        'content': (
            'MD5 and SHA-1 are cryptographically broken against classical collision attacks and prohibited for all digital '
            'signatures, authentication, and certificates. Remediate immediately by replacing with SHA-256, SHA-512, '
            'or SHA-3 (Keccak). If MD5 was used solely for non-security checksums or cache keys, mark as false positive.'
        )
    },
    {
        'title': 'Quantum Resistance of Symmetric Encryption: AES and ChaCha20',
        'category': 'QUANTUM_SAFE_CLASSICAL',
        'source': 'NIST Quantum Advisory',
        'content': (
            "Grover's algorithm reduces the effective brute-force key strength of symmetric ciphers by half. "
            'Therefore, AES-128 offers 64 bits of post-quantum security (marginal). AES-256 and ChaCha20-Poly1305 provide '
            'at least 128 bits of quantum security and are fully quantum-safe. No immediate algorithm change is required '
            'if 256-bit symmetric keys are utilized.'
        )
    }
]

async def seed():
    store = VectorStore()

    print('Ensuring Qdrant collection exists...')

    await store.init_collection()

    print(f'Seeding {len(KNOWLEDGE_DOCUMENTS)} PQC knowledge documents...')

    for idx, doc in enumerate(KNOWLEDGE_DOCUMENTS, start=1):
        print(f'[{idx}/{len(KNOWLEDGE_DOCUMENTS)}] Embedding & inserting: {doc['title']}')

        await store.add_document(
            title=doc['title'],
            category=doc['category'],
            content=doc['content'],
            source=doc['source']
        )

    print('\n✅ Knowledge base successfully seeded in Qdrant!')

if __name__ == '__main__':
    asyncio.run(seed())
