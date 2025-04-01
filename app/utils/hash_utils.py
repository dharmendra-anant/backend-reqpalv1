import hashlib

def hash_file_content(content: bytes) -> str:
    """
    Generate a SHA-256 hash for the given file content.

    Args:
        content (bytes): The binary content of the file.

    Returns:
        str: A SHA-256 hash as a hex string.
    """
    return hashlib.sha256(content).hexdigest()