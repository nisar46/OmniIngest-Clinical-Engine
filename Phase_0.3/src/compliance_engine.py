import re
import hashlib
import pandas as pd
from datetime import datetime, timedelta
# [PHASE 0.3 LINK] Connecting the Brain to the Vault
from .database import rule_8_3_incinerator 

class ComplianceEngine:
    """
    SME Engine for India DPDP 2026.
    Triggers 'Rule 8.3 Incineration' based on Consent & Retention.
    """
    def __init__(self, threshold_days=365):
        self.threshold_date = datetime.now() - timedelta(days=threshold_days)
        self.notice_regex = r'^N-2026-[A-Z]{3,4}-v\d+\.\d+$'

    def evaluate_record(self, consent_status, notice_date):
        """SME Logic: Determines if a record must be incinerated."""
        consent = str(consent_status).upper()
        
        # 1. Rule 8: Consent Revocation
        if consent == 'REVOKED':
            return "PURGE_REQUIRED", "CONSENT_REVOKED"
        
        # 2. Rule 3: Retention Expiry
        if notice_date:
            try:
                n_date = pd.to_datetime(notice_date)
                if n_date < self.threshold_date:
                    return "PURGE_REQUIRED", "NOTICE_EXPIRED"
            except: pass
            
        return "SAFE", "N/A"

    def execute_compliance_check(self, abha_id, consent_status, notice_date):
        """
        [THE INCINERATOR TRIGGER]
        Phase 0.3 Upgrade: Performs the Hard SQL Delete if status is PURGE_REQUIRED.
        """
        status, reason = self.evaluate_record(consent_status, notice_date)
        
        if status == "PURGE_REQUIRED":
            # TRIGGER THE DATABASE VAULT
            rule_8_3_incinerator(abha_id)
            return True, reason
        return False, "N/A"

# --- FHIR R5 INTEROPERABILITY (SME SIGNATURE) ---
def verify_fhir_structure(resource):
    """Lead Auditor Check: Validates FHIR R5 Patient structure."""
    if "resourceType" in resource and resource["resourceType"] == "Patient":
        name_block = resource.get("name", [])
        if not name_block or not isinstance(name_block, list) or "text" not in name_block[0]:
            return False
        return True
    return False
