import os
import math
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import struct


def generate_id() -> str:
    """Generate a unique ID for records."""
    return str(uuid.uuid4())


def get_file_extension(file_path: str) -> str:
    """Extract file extension from path."""
    _, ext = os.path.splitext(file_path)
    return ext.lower().lstrip(".")


def get_file_name(file_path: str) -> str:
    """Extract file name from path."""
    return os.path.basename(file_path)


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return os.path.getsize(file_path)
        return 0
    except (OSError, PermissionError):
        return 0


def calculate_file_entropy(file_path: str) -> float:
    """
    Calculate Shannon entropy of a file.
    High entropy (> 7.0) may indicate encryption or compression.

    Args:
        file_path: Path to the file

    Returns:
        Entropy value between 0.0 and 8.0
    """
    try:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return 0.0

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return 0.0

        # Read file in chunks for large files
        byte_counts = [0] * 256
        with open(file_path, "rb") as f:
            chunk = f.read(65536)
            while chunk:
                for byte in chunk:
                    byte_counts[byte] += 1
                chunk = f.read(65536)

        entropy = 0.0
        for count in byte_counts:
            if count > 0:
                probability = count / file_size
                entropy -= probability * math.log2(probability)

        return round(entropy, 4)

    except (OSError, PermissionError, IOError):
        return 0.0


def calculate_file_hash(file_path: str) -> Optional[str]:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        SHA256 hex digest or None
    """
    try:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return None

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            chunk = f.read(65536)
            while chunk:
                sha256.update(chunk)
                chunk = f.read(65536)

        return sha256.hexdigest()

    except (OSError, PermissionError):
        return None


def bytes_to_gb(bytes_value: int) -> float:
    """Convert bytes to gigabytes."""
    return round(bytes_value / (1024 ** 3), 2)


def bytes_to_mb(bytes_value: int) -> float:
    """Convert bytes to megabytes."""
    return round(bytes_value / (1024 ** 2), 2)


def is_suspicious_extension(extension: str) -> bool:
    """
    Check if a file extension is commonly associated with ransomware.

    Args:
        extension: File extension without dot

    Returns:
        True if suspicious
    """
    # Common ransomware file extensions
    suspicious_extensions = {
        "encrypted", "enc", "crypt", "crypted", "crypto",
        "locked", "lock", "locker",
        "ransom", "ransomed",
        "wcry", "wncry", "wncryt",
        "cerber", "cerber2", "cerber3",
        "zepto", "locky",
        "thor", "odin",
        "r5a", "r4a",
        "zzz", "xxx",
        "pays", "pays2",
        "rmd",
        "ecc", "ezz", "exx", "xyz",
        "abc", "aaa",
        "micro", "darkness", "nochance",
        "cryptolocker",
    }
    return extension.lower() in suspicious_extensions


def detect_suspicious_keywords(file_path: str) -> List[str]:
    """
    Scan file for suspicious keywords related to ransomware.

    Args:
        file_path: Path to file

    Returns:
        List of detected suspicious keywords
    """
    suspicious_keywords = [
        "your files have been encrypted",
        "all your files",
        "bitcoin",
        "btc payment",
        "decrypt your files",
        "ransom",
        "pay to recover",
        "your data is encrypted",
        "readme.txt",
        "how to decrypt",
        "decryption key",
        "tor browser",
        "onion link",
    ]

    found_keywords = []

    try:
        # Only scan text-like files under 5MB
        file_size = get_file_size(file_path)
        if file_size == 0 or file_size > 5 * 1024 * 1024:
            return found_keywords

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith("text"):
            return found_keywords

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
            for keyword in suspicious_keywords:
                if keyword in content:
                    found_keywords.append(keyword)

    except (OSError, PermissionError, UnicodeDecodeError):
        pass

    return found_keywords


def get_mime_type(file_path: str) -> Optional[str]:
    """Get MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO 8601 string."""
    return dt.isoformat() + "Z"


def sanitize_path(path: str) -> str:
    """Sanitize a file path to prevent path traversal."""
    # Normalize the path
    normalized = os.path.normpath(path)
    return normalized


def calculate_risk_score(
    confidence: float,
    is_ransomware: bool,
    threat_level: str,
    entropy: float,
    suspicious_extensions: bool,
    rapid_changes: int,
) -> float:
    """
    Calculate overall risk score from 0-100.

    Args:
        confidence: ML model confidence (0-1)
        is_ransomware: Whether classified as ransomware
        threat_level: Threat level string
        entropy: File entropy
        suspicious_extensions: Whether extension is suspicious
        rapid_changes: Number of rapid file changes

    Returns:
        Risk score 0-100
    """
    score = 0.0

    # Base score from confidence
    score += confidence * 40

    # Ransomware classification bonus
    if is_ransomware:
        score += 25

    # Threat level scoring
    level_scores = {
        "critical": 20,
        "high": 15,
        "medium": 10,
        "low": 5,
        "safe": 0,
    }
    score += level_scores.get(threat_level, 0)

    # Entropy scoring (high entropy suggests encryption)
    if entropy > 7.5:
        score += 10
    elif entropy > 7.0:
        score += 7
    elif entropy > 6.5:
        score += 3

    # Suspicious extension
    if suspicious_extensions:
        score += 3

    # Rapid changes
    if rapid_changes > 100:
        score += 2
    elif rapid_changes > 50:
        score += 1

    return min(round(score, 2), 100.0)