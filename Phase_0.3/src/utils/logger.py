import re
import logging
import sys

# Configure standard logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [OMNI-INGEST] - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OmniIngest_Secure")

# PII Regex Patterns (simplified for demo speed, robust for key identifiers)
PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "ABHA": r'\b\d{2}-\d{4}-\d{4}-\d{4}\b',  # 12-3456-7890-1234
    "PHONE": r'\b(?:\+91|91)?\d{10}\b',
    "AADHAAR": r'\b\d{4}\s\d{4}\s\d{4}\b'
}

def safe_log(message: str, level: str = "INFO"):
    """
    Logs a message with PII automatically redacted.
    Used to prevent 'Data Leakage' in production logs (DPDP Compliance).
    """
    redacted_msg = message
    
    # Apply Redaction
    for p_name, pattern in PATTERNS.items():
        redacted_msg = re.sub(pattern, f"[REDACTED_{p_name}]", redacted_msg)
    
    # Log to system
    if level.upper() == "ERROR":
        logger.error(redacted_msg)
    elif level.upper() == "WARNING":
        logger.warning(redacted_msg)
    else:
        logger.info(redacted_msg)

    return redacted_msg
