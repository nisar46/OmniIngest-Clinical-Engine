
import pdfplumber
import re
import polars as pl
from datetime import datetime

def extract_from_pdf(file_path):
    """
    Extracts clinical data from PDF reports using Heuristics.
    Returns a Polars DataFrame with standard columns.
    """
    text_content = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text_content += page.extract_text() or ""
    except Exception as e:
        print(f"PDF Read Error: {e}")
        return pl.DataFrame()

    # Heuristic Parsing
    data = {}
    
    # 1. Patient Name
    # Look for "Name:", "Patient:", "Pt Name:" followed by text
    name_match = re.search(r'(?:Name|Patient Name|Pt Name|Patient)\s*[:\-\.]\s*([A-Za-z\s\.]+)', text_content, re.IGNORECASE)
    if name_match:
        data['Patient_Name'] = name_match.group(1).strip()
    else:
        # Fallback: Look for "Mr./Ms."
        name_match_2 = re.search(r'(?:Mr\.|Ms\.|Mrs\.)\s*([A-Za-z\s]+)', text_content)
        data['Patient_Name'] = name_match_2.group(0).strip() if name_match_2 else None

    # 2. ABHA ID (Regex for ##-####-####-####)
    abha_match = re.search(r'\b(\d{2}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4})\b', text_content)
    if abha_match:
        data['ABHA_ID'] = abha_match.group(1).replace(" ", "-")
    else:
        # Try PHR address
        abha_addr = re.search(r'\b([a-zA-Z0-9.]+@sbx)\b', text_content)
        data['ABHA_ID'] = abha_addr.group(1) if abha_addr else None

    # 3. Clinical Payload (Diagnosis/Report)
    # Strategy: Grab text after "Diagnosis:" or "Impression:"
    diagnosis_match = re.search(r'(?:Diagnosis|Impression|Conclusion)\s*[:\-\.]\s*(.*)', text_content, re.IGNORECASE)
    if diagnosis_match:
        data['Clinical_Payload'] = diagnosis_match.group(1).strip()
    else:
        # Fallback: Just take the first 200 chars as summary
        data['Clinical_Payload'] = text_content[:200].replace("\n", " ") + "..."

    # 4. Standard Fields
    data['Notice_ID'] = f"N-2026-PDF-{datetime.now().strftime('%H%M%S')}"
    data['Notice_Date'] = datetime.now().strftime("%Y-%m-%d")
    data['Consent_Status'] = "GRANTED" # Implicit for uploaded reports in this demo workflow

    # Create Polars DF
    return pl.DataFrame([data])
