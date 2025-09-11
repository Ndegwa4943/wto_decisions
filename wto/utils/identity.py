# wto/utils/identity.py
import hashlib, uuid

def doc_uuid(key: bytes) -> uuid.UUID:
    """Deterministic UUID from file bytes (SHA-256 => first 16 bytes)."""
    return uuid.UUID(bytes=hashlib.sha256(key).digest()[:16])
