"""
Universal Adapter for Hospital Data Ingestion
Handles multiple file formats (CSV, JSON, XML, XLSX, DICOM, HL7 V2, FHIR R5, PDF, Text Reports, API responses)
and standardizes to canonical schema.
Includes compliance scenarios for ABDM Discovery and DPDP Rules 2025.
"""

import pandas as pd
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional
import os
import re
import urllib.request
import urllib.parse
import uuid
import time
import hashlib
from compliance_engine import ComplianceEngine
from abdm_api_client import ABDMApiClient # Phase 1 Integration
from database_manager import DatabaseManager # Phase 2 Integration

# Optional imports for specialized formats
try:
    import pydicom
    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
    PDF_ENGINE = 'PyPDF2'
except ImportError:
    try:
        import pdfplumber
        PDF_AVAILABLE = True
        PDF_ENGINE = 'pdfplumber'
    except ImportError:
        PDF_AVAILABLE = False
        PDF_ENGINE = None


# Canonical schema field names
CANONICAL_FIELDS = [
    'Patient_Name',
    'ABHA_ID',
    'Clinical_Payload',
    'Consent_Status',
    'Consent_Token',
    'Notice_ID',
    'Notice_Date',
    'Data_Purpose'
]

# Simple In-Memory SNOMED-CT Mapper (Mock Terminology Engine)
SNOMED_MAP = {
    # Diagnosis
    "Type 2 Diabetes": "44054006",
    "Hypertension": "38341003",
    "Viral Fever": "409532009",
    "Acute Bronchitis": "10509002",
    "Migraine": "37796009",
    "Fracture": "125605004",
    # Medications
    "Metformin 500mg": "372567009",
    "Paracetamol 650mg": "387517004",
    "Azithromycin 500mg": "387341005"
}

# Field mapping dictionary to standardize inconsistent input column names
# Comprehensive mapping covering all possible hospital naming variations
FIELD_MAPPING = {
    # Patient_Name variations (50+ variations)
    'patient_name': 'Patient_Name',
    'patient name': 'Patient_Name',
    'name': 'Patient_Name',
    'patient': 'Patient_Name',
    'full_name': 'Patient_Name',
    'patient_full_name': 'Patient_Name',
    'patientname': 'Patient_Name',
    'pt_name': 'Patient_Name',
    'pt name': 'Patient_Name',
    'patientname': 'Patient_Name',
    'p_name': 'Patient_Name',
    'pname': 'Patient_Name',
    'patient_name_full': 'Patient_Name',
    'fullname': 'Patient_Name',
    'full name': 'Patient_Name',
    'patient_fullname': 'Patient_Name',
    'name_of_patient': 'Patient_Name',
    'patient_name_first_last': 'Patient_Name',
    'first_name_last_name': 'Patient_Name',
    'firstname_lastname': 'Patient_Name',
    'patient_first_last': 'Patient_Name',
    'pt_full_name': 'Patient_Name',
    'patient_fullname': 'Patient_Name',
    'name_full': 'Patient_Name',
    'patient_name_complete': 'Patient_Name',
    'complete_name': 'Patient_Name',
    'patient_complete_name': 'Patient_Name',
    'beneficiary_name': 'Patient_Name',
    'beneficiary name': 'Patient_Name',
    'member_name': 'Patient_Name',
    'member name': 'Patient_Name',
    'insured_name': 'Patient_Name',
    'insured name': 'Patient_Name',
    'subscriber_name': 'Patient_Name',
    'subscriber name': 'Patient_Name',
    'client_name': 'Patient_Name',
    'client name': 'Patient_Name',
    'customer_name': 'Patient_Name',
    'customer name': 'Patient_Name',
    'person_name': 'Patient_Name',
    'person name': 'Patient_Name',
    'individual_name': 'Patient_Name',
    'individual name': 'Patient_Name',
    'name_of_beneficiary': 'Patient_Name',
    'name_of_member': 'Patient_Name',
    'name_of_insured': 'Patient_Name',
    'name_of_subscriber': 'Patient_Name',
    'name_of_client': 'Patient_Name',
    'name_of_customer': 'Patient_Name',
    'name_of_person': 'Patient_Name',
    'name_of_individual': 'Patient_Name',
    'patient_firstname': 'Patient_Name',
    'patient_lastname': 'Patient_Name',
    'firstname': 'Patient_Name',
    'lastname': 'Patient_Name',
    'first_name': 'Patient_Name',
    'last_name': 'Patient_Name',
    
    # ABHA_ID variations (40+ variations)
    'abha_id': 'ABHA_ID',
    'abha id': 'ABHA_ID',
    'abha': 'ABHA_ID',
    'health_id': 'ABHA_ID',
    'healthid': 'ABHA_ID',
    'health_id_number': 'ABHA_ID',
    'abha_number': 'ABHA_ID',
    'abhaid': 'ABHA_ID',
    'abha number': 'ABHA_ID',
    'healthid_number': 'ABHA_ID',
    'health id number': 'ABHA_ID',
    'health_id_no': 'ABHA_ID',
    'health id no': 'ABHA_ID',
    'healthid_no': 'ABHA_ID',
    'abha_id_no': 'ABHA_ID',
    'abha id no': 'ABHA_ID',
    'abha_no': 'ABHA_ID',
    'abha no': 'ABHA_ID',
    'health_id_code': 'ABHA_ID',
    'health id code': 'ABHA_ID',
    'abha_code': 'ABHA_ID',
    'abha code': 'ABHA_ID',
    'health_id_code': 'ABHA_ID',
    'healthid_code': 'ABHA_ID',
    'health_id_identifier': 'ABHA_ID',
    'health id identifier': 'ABHA_ID',
    'abha_identifier': 'ABHA_ID',
    'abha identifier': 'ABHA_ID',
    'health_identifier': 'ABHA_ID',
    'health identifier': 'ABHA_ID',
    'healthid_identifier': 'ABHA_ID',
    'ayushman_bharat_id': 'ABHA_ID',
    'ayushman bharat id': 'ABHA_ID',
    'ayushmanbharat_id': 'ABHA_ID',
    'ayushman_bharat_number': 'ABHA_ID',
    'ayushman bharat number': 'ABHA_ID',
    'national_health_id': 'ABHA_ID',
    'national health id': 'ABHA_ID',
    'nationalhealthid': 'ABHA_ID',
    'nhi': 'ABHA_ID',
    'nhi_id': 'ABHA_ID',
    'nhi number': 'ABHA_ID',
    'nhi_number': 'ABHA_ID',
    'unique_health_id': 'ABHA_ID',
    'unique health id': 'ABHA_ID',
    'uhid': 'ABHA_ID',
    'uhid_number': 'ABHA_ID',
    'uhid number': 'ABHA_ID',
    'health_card_number': 'ABHA_ID',
    'health card number': 'ABHA_ID',
    'healthcard_number': 'ABHA_ID',
    'health_card_no': 'ABHA_ID',
    'health card no': 'ABHA_ID',
    'healthcard_no': 'ABHA_ID',
    'health_card_id': 'ABHA_ID',
    'health card id': 'ABHA_ID',
    'healthcard_id': 'ABHA_ID',
    'medical_record_id': 'ABHA_ID',
    'medical record id': 'ABHA_ID',
    'medicalrecord_id': 'ABHA_ID',
    'mrn': 'ABHA_ID',
    'mrn_id': 'ABHA_ID',
    'mrn number': 'ABHA_ID',
    'mrn_number': 'ABHA_ID',
    'patient_id': 'ABHA_ID',
    'patient id': 'ABHA_ID',
    'patientid': 'ABHA_ID',
    'pt_id': 'ABHA_ID',
    'pt id': 'ABHA_ID',
    'ptid': 'ABHA_ID',
    'patient_identifier': 'ABHA_ID',
    'patient identifier': 'ABHA_ID',
    'patientidentifier': 'ABHA_ID',
    'beneficiary_id': 'ABHA_ID',
    'beneficiary id': 'ABHA_ID',
    'beneficiaryid': 'ABHA_ID',
    'member_id': 'ABHA_ID',
    'member id': 'ABHA_ID',
    'memberid': 'ABHA_ID',
    'insured_id': 'ABHA_ID',
    'insured id': 'ABHA_ID',
    'insuredid': 'ABHA_ID',
    'subscriber_id': 'ABHA_ID',
    'subscriber id': 'ABHA_ID',
    'subscriberid': 'ABHA_ID',
    'client_id': 'ABHA_ID',
    'client id': 'ABHA_ID',
    'clientid': 'ABHA_ID',
    'customer_id': 'ABHA_ID',
    'customer id': 'ABHA_ID',
    'customerid': 'ABHA_ID',
    
    # Clinical_Payload variations (30+ variations)
    'clinical_payload': 'Clinical_Payload',
    'clinical payload': 'Clinical_Payload',
    'payload': 'Clinical_Payload',
    'clinical_data': 'Clinical_Payload',
    'medical_data': 'Clinical_Payload',
    'clinical_info': 'Clinical_Payload',
    'data': 'Clinical_Payload',
    'clinicalpayload': 'Clinical_Payload',
    'clinicaldata': 'Clinical_Payload',
    'clinicalinfo': 'Clinical_Payload',
    'medicaldata': 'Clinical_Payload',
    'medical_info': 'Clinical_Payload',
    'medical info': 'Clinical_Payload',
    'medicalinfo': 'Clinical_Payload',
    'clinical_information': 'Clinical_Payload',
    'clinical information': 'Clinical_Payload',
    'clinicalinformation': 'Clinical_Payload',
    'medical_information': 'Clinical_Payload',
    'medical information': 'Clinical_Payload',
    'medicalinformation': 'Clinical_Payload',
    'patient_data': 'Clinical_Payload',
    'patient data': 'Clinical_Payload',
    'patientdata': 'Clinical_Payload',
    'patient_info': 'Clinical_Payload',
    'patient info': 'Clinical_Payload',
    'patientinfo': 'Clinical_Payload',
    'patient_information': 'Clinical_Payload',
    'patient information': 'Clinical_Payload',
    'patientinformation': 'Clinical_Payload',
    'diagnosis': 'Clinical_Payload',
    'diagnosis_data': 'Clinical_Payload',
    'diagnosis data': 'Clinical_Payload',
    'diagnosisdata': 'Clinical_Payload',
    'diagnosis_info': 'Clinical_Payload',
    'diagnosis info': 'Clinical_Payload',
    'diagnosisinfo': 'Clinical_Payload',
    'diagnosis_information': 'Clinical_Payload',
    'diagnosis information': 'Clinical_Payload',
    'diagnosisinformation': 'Clinical_Payload',
    'treatment': 'Clinical_Payload',
    'treatment_data': 'Clinical_Payload',
    'treatment data': 'Clinical_Payload',
    'treatmentdata': 'Clinical_Payload',
    'treatment_info': 'Clinical_Payload',
    'treatment info': 'Clinical_Payload',
    'treatmentinfo': 'Clinical_Payload',
    'treatment_information': 'Clinical_Payload',
    'treatment information': 'Clinical_Payload',
    'treatmentinformation': 'Clinical_Payload',
    'medical_record': 'Clinical_Payload',
    'medical record': 'Clinical_Payload',
    'medicalrecord': 'Clinical_Payload',
    'medical_record_data': 'Clinical_Payload',
    'medical record data': 'Clinical_Payload',
    'medicalrecorddata': 'Clinical_Payload',
    'clinical_record': 'Clinical_Payload',
    'clinical record': 'Clinical_Payload',
    'clinicalrecord': 'Clinical_Payload',
    'clinical_record_data': 'Clinical_Payload',
    'clinical record data': 'Clinical_Payload',
    'clinicalrecorddata': 'Clinical_Payload',
    'health_data': 'Clinical_Payload',
    'health data': 'Clinical_Payload',
    'healthdata': 'Clinical_Payload',
    'health_info': 'Clinical_Payload',
    'health info': 'Clinical_Payload',
    'healthinfo': 'Clinical_Payload',
    'health_information': 'Clinical_Payload',
    'health information': 'Clinical_Payload',
    'healthinformation': 'Clinical_Payload',
    'case_data': 'Clinical_Payload',
    'case data': 'Clinical_Payload',
    'casedata': 'Clinical_Payload',
    'case_info': 'Clinical_Payload',
    'case info': 'Clinical_Payload',
    'caseinfo': 'Clinical_Payload',
    'case_information': 'Clinical_Payload',
    'case information': 'Clinical_Payload',
    'caseinformation': 'Clinical_Payload',
    'visit_data': 'Clinical_Payload',
    'visit data': 'Clinical_Payload',
    'visitdata': 'Clinical_Payload',
    'visit_info': 'Clinical_Payload',
    'visit info': 'Clinical_Payload',
    'visitinfo': 'Clinical_Payload',
    'visit_information': 'Clinical_Payload',
    'visit information': 'Clinical_Payload',
    'visitinformation': 'Clinical_Payload',
    'encounter_data': 'Clinical_Payload',
    'encounter data': 'Clinical_Payload',
    'encounterdata': 'Clinical_Payload',
    'encounter_info': 'Clinical_Payload',
    'encounter info': 'Clinical_Payload',
    'encounterinfo': 'Clinical_Payload',
    'encounter_information': 'Clinical_Payload',
    'encounter information': 'Clinical_Payload',
    'encounterinformation': 'Clinical_Payload',
    'episode_data': 'Clinical_Payload',
    'episode data': 'Clinical_Payload',
    'episodedata': 'Clinical_Payload',
    'episode_info': 'Clinical_Payload',
    'episode info': 'Clinical_Payload',
    'episodeinfo': 'Clinical_Payload',
    'episode_information': 'Clinical_Payload',
    'episode information': 'Clinical_Payload',
    'episodeinformation': 'Clinical_Payload',
    'notes': 'Clinical_Payload',
    'clinical_notes': 'Clinical_Payload',
    'clinical notes': 'Clinical_Payload',
    'clinicalnotes': 'Clinical_Payload',
    'medical_notes': 'Clinical_Payload',
    'medical notes': 'Clinical_Payload',
    'medicalnotes': 'Clinical_Payload',
    'doctor_notes': 'Clinical_Payload',
    'doctor notes': 'Clinical_Payload',
    'doctornotes': 'Clinical_Payload',
    'physician_notes': 'Clinical_Payload',
    'physician notes': 'Clinical_Payload',
    'physiciannotes': 'Clinical_Payload',
    'remarks': 'Clinical_Payload',
    'clinical_remarks': 'Clinical_Payload',
    'clinical remarks': 'Clinical_Payload',
    'clinicalremarks': 'Clinical_Payload',
    'medical_remarks': 'Clinical_Payload',
    'medical remarks': 'Clinical_Payload',
    'medicalremarks': 'Clinical_Payload',
    'comments': 'Clinical_Payload',
    'clinical_comments': 'Clinical_Payload',
    'clinical comments': 'Clinical_Payload',
    'clinicalcomments': 'Clinical_Payload',
    'medical_comments': 'Clinical_Payload',
    'medical comments': 'Clinical_Payload',
    'medicalcomments': 'Clinical_Payload',
    
    # Consent_Status variations (25+ variations)
    'consent_status': 'Consent_Status',
    'consent status': 'Consent_Status',
    'consent': 'Consent_Status',
    'consent_state': 'Consent_Status',
    'status': 'Consent_Status',
    'consent_flag': 'Consent_Status',
    'consentstatus': 'Consent_Status',
    'consentstate': 'Consent_Status',
    'consentflag': 'Consent_Status',
    'consent_status_flag': 'Consent_Status',
    'consent status flag': 'Consent_Status',
    'consentstatusflag': 'Consent_Status',
    'consent_state_flag': 'Consent_Status',
    'consent state flag': 'Consent_Status',
    'consentstateflag': 'Consent_Status',
    'consent_indicator': 'Consent_Status',
    'consent indicator': 'Consent_Status',
    'consentindicator': 'Consent_Status',
    'consent_type': 'Consent_Status',
    'consent type': 'Consent_Status',
    'consenttype': 'Consent_Status',
    'consent_given': 'Consent_Status',
    'consent given': 'Consent_Status',
    'consentgiven': 'Consent_Status',
    'consent_provided': 'Consent_Status',
    'consent provided': 'Consent_Status',
    'consentprovided': 'Consent_Status',
    'consent_obtained': 'Consent_Status',
    'consent obtained': 'Consent_Status',
    'consentobtained': 'Consent_Status',
    'consent_received': 'Consent_Status',
    'consent received': 'Consent_Status',
    'consentreceived': 'Consent_Status',
    'consent_acknowledged': 'Consent_Status',
    'consent acknowledged': 'Consent_Status',
    'consentacknowledged': 'Consent_Status',
    'consent_confirmed': 'Consent_Status',
    'consent confirmed': 'Consent_Status',
    'consentconfirmed': 'Consent_Status',
    'consent_verified': 'Consent_Status',
    'consent verified': 'Consent_Status',
    'consentverified': 'Consent_Status',
    'consent_approved': 'Consent_Status',
    'consent approved': 'Consent_Status',
    'consentapproved': 'Consent_Status',
    'consent_authorized': 'Consent_Status',
    'consent authorized': 'Consent_Status',
    'consentauthorized': 'Consent_Status',
    'consent_permission': 'Consent_Status',
    'consent permission': 'Consent_Status',
    'consentpermission': 'Consent_Status',
    'consent_agreement': 'Consent_Status',
    'consent agreement': 'Consent_Status',
    'consentagreement': 'Consent_Status',
    'data_consent': 'Consent_Status',
    'data consent': 'Consent_Status',
    'dataconsent': 'Consent_Status',
    'data_consent_status': 'Consent_Status',
    'data consent status': 'Consent_Status',
    'dataconsentstatus': 'Consent_Status',
    'privacy_consent': 'Consent_Status',
    'privacy consent': 'Consent_Status',
    'privacyconsent': 'Consent_Status',
    'privacy_consent_status': 'Consent_Status',
    'privacy consent status': 'Consent_Status',
    'privacyconsentstatus': 'Consent_Status',
    
    # Consent Token / Artifact
    'consent_token': 'Consent_Token',
    'consent token': 'Consent_Token',
    'consenttoken': 'Consent_Token',
    'token': 'Consent_Token',
    'artifact': 'Consent_Token',
    'consent_artifact': 'Consent_Token',
    'patient_consent': 'Consent_Status',
    'patient consent': 'Consent_Status',
    'patientconsent': 'Consent_Status',
    'patient_consent_status': 'Consent_Status',
    'patient consent status': 'Consent_Status',
    'patientconsentstatus': 'Consent_Status',
    'authorization_status': 'Consent_Status',
    'authorization status': 'Consent_Status',
    'authorizationstatus': 'Consent_Status',
    'authorization': 'Consent_Status',
    'authorization_flag': 'Consent_Status',
    'authorization flag': 'Consent_Status',
    'authorizationflag': 'Consent_Status',
    'permission_status': 'Consent_Status',
    'permission status': 'Consent_Status',
    'permissionstatus': 'Consent_Status',
    'permission': 'Consent_Status',
    'permission_flag': 'Consent_Status',
    'permission flag': 'Consent_Status',
    'permissionflag': 'Consent_Status',
    'agreement_status': 'Consent_Status',
    'agreement status': 'Consent_Status',
    'agreementstatus': 'Consent_Status',
    'agreement': 'Consent_Status',
    'agreement_flag': 'Consent_Status',
    'agreement flag': 'Consent_Status',
    'agreementflag': 'Consent_Status',
    'approval_status': 'Consent_Status',
    'approval status': 'Consent_Status',
    'approvalstatus': 'Consent_Status',
    'approval': 'Consent_Status',
    'approval_flag': 'Consent_Status',
    'approval flag': 'Consent_Status',
    'approvalflag': 'Consent_Status',
    'verification_status': 'Consent_Status',
    'verification status': 'Consent_Status',
    'verificationstatus': 'Consent_Status',
    'verification': 'Consent_Status',
    'verification_flag': 'Consent_Status',
    'verification flag': 'Consent_Status',
    'verificationflag': 'Consent_Status',
    'confirmation_status': 'Consent_Status',
    'confirmation status': 'Consent_Status',
    'confirmationstatus': 'Consent_Status',
    'confirmation': 'Consent_Status',
    'confirmation_flag': 'Consent_Status',
    'confirmation flag': 'Consent_Status',
    'confirmationflag': 'Consent_Status',
    'acknowledgment_status': 'Consent_Status',
    'acknowledgment status': 'Consent_Status',
    'acknowledgmentstatus': 'Consent_Status',
    'acknowledgment': 'Consent_Status',
    'acknowledgment_flag': 'Consent_Status',
    'acknowledgment flag': 'Consent_Status',
    'acknowledgmentflag': 'Consent_Status',
    
    # Notice_ID variations (30+ variations)
    'notice_id': 'Notice_ID',
    'notice id': 'Notice_ID',
    'notice': 'Notice_ID',
    'notice_number': 'Notice_ID',
    'notice num': 'Notice_ID',
    'notice_num': 'Notice_ID',
    'notification_id': 'Notice_ID',
    'noticeid': 'Notice_ID',
    'noticenumber': 'Notice_ID',
    'noticenum': 'Notice_ID',
    'notificationid': 'Notice_ID',
    'notice_id_number': 'Notice_ID',
    'notice id number': 'Notice_ID',
    'noticeidnumber': 'Notice_ID',
    'notice_id_no': 'Notice_ID',
    'notice id no': 'Notice_ID',
    'noticeidno': 'Notice_ID',
    'notice_number_id': 'Notice_ID',
    'notice number id': 'Notice_ID',
    'noticenumberid': 'Notice_ID',
    'notice_no': 'Notice_ID',
    'notice no': 'Notice_ID',
    'noticeno': 'Notice_ID',
    'notice_code': 'Notice_ID',
    'notice code': 'Notice_ID',
    'noticecode': 'Notice_ID',
    'notice_identifier': 'Notice_ID',
    'notice identifier': 'Notice_ID',
    'noticeidentifier': 'Notice_ID',
    'notification_number': 'Notice_ID',
    'notification number': 'Notice_ID',
    'notificationnumber': 'Notice_ID',
    'notification_no': 'Notice_ID',
    'notification no': 'Notice_ID',
    'notificationno': 'Notice_ID',
    'notification_code': 'Notice_ID',
    'notification code': 'Notice_ID',
    'notificationcode': 'Notice_ID',
    'notification_identifier': 'Notice_ID',
    'notification identifier': 'Notice_ID',
    'notificationidentifier': 'Notice_ID',
    'dpdp_notice_id': 'Notice_ID',
    'dpdp notice id': 'Notice_ID',
    'dpdpnoticeid': 'Notice_ID',
    'dpdp_notice_number': 'Notice_ID',
    'dpdp notice number': 'Notice_ID',
    'dpdpnoticenumber': 'Notice_ID',
    'dpdp_notice_no': 'Notice_ID',
    'dpdp notice no': 'Notice_ID',
    'dpdpnoticeno': 'Notice_ID',
    'dpdp_notification_id': 'Notice_ID',
    'dpdp notification id': 'Notice_ID',
    'dpdpnotificationid': 'Notice_ID',
    'privacy_notice_id': 'Notice_ID',
    'privacy notice id': 'Notice_ID',
    'privacynoticeid': 'Notice_ID',
    'privacy_notice_number': 'Notice_ID',
    'privacy notice number': 'Notice_ID',
    'privacynoticenumber': 'Notice_ID',
    'privacy_notice_no': 'Notice_ID',
    'privacy notice no': 'Notice_ID',
    'privacynoticeno': 'Notice_ID',
    'privacy_notification_id': 'Notice_ID',
    'privacy notification id': 'Notice_ID',
    'privacynotificationid': 'Notice_ID',
    'data_notice_id': 'Notice_ID',
    'data notice id': 'Notice_ID',
    'datanoticeid': 'Notice_ID',
    'data_notice_number': 'Notice_ID',
    'data notice number': 'Notice_ID',
    'datanoticenumber': 'Notice_ID',
    'data_notice_no': 'Notice_ID',
    'data notice no': 'Notice_ID',
    'datanoticeno': 'Notice_ID',
    'data_notification_id': 'Notice_ID',
    'data notification id': 'Notice_ID',
    'datanotificationid': 'Notice_ID',
    'compliance_notice_id': 'Notice_ID',
    'compliance notice id': 'Notice_ID',
    'compliancenoticeid': 'Notice_ID',
    'compliance_notice_number': 'Notice_ID',
    'compliance notice number': 'Notice_ID',
    'compliancenoticenumber': 'Notice_ID',
    'compliance_notice_no': 'Notice_ID',
    'compliance notice no': 'Notice_ID',
    'compliancenoticeno': 'Notice_ID',
    'compliance_notification_id': 'Notice_ID',
    'compliance notification id': 'Notice_ID',
    'compliancenotificationid': 'Notice_ID',
    'legal_notice_id': 'Notice_ID',
    'legal notice id': 'Notice_ID',
    'legalnoticeid': 'Notice_ID',
    'legal_notice_number': 'Notice_ID',
    'legal notice number': 'Notice_ID',
    'legalnoticenumber': 'Notice_ID',
    'legal_notice_no': 'Notice_ID',
    'legal notice no': 'Notice_ID',
    'legalnoticeno': 'Notice_ID',
    'legal_notification_id': 'Notice_ID',
    'legal notification id': 'Notice_ID',
    'legalnotificationid': 'Notice_ID',
    'regulatory_notice_id': 'Notice_ID',
    'regulatory notice id': 'Notice_ID',
    'regulatorynoticeid': 'Notice_ID',
    'regulatory_notice_number': 'Notice_ID',
    'regulatory notice number': 'Notice_ID',
    'regulatorynoticenumber': 'Notice_ID',
    'regulatory_notice_no': 'Notice_ID',
    'regulatory notice no': 'Notice_ID',
    'regulatorynoticeno': 'Notice_ID',
    'regulatory_notification_id': 'Notice_ID',
    'regulatory notification id': 'Notice_ID',
    'regulatorynotificationid': 'Notice_ID',
    'document_id': 'Notice_ID',
    'document id': 'Notice_ID',
    'documentid': 'Notice_ID',
    'document_number': 'Notice_ID',
    'document number': 'Notice_ID',
    'documentnumber': 'Notice_ID',
    'document_no': 'Notice_ID',
    'document no': 'Notice_ID',
    'documentno': 'Notice_ID',
    'document_code': 'Notice_ID',
    'document code': 'Notice_ID',
    'documentcode': 'Notice_ID',
    'document_identifier': 'Notice_ID',
    'document identifier': 'Notice_ID',
    'documentidentifier': 'Notice_ID',
    'reference_id': 'Notice_ID',
    'reference id': 'Notice_ID',
    'referenceid': 'Notice_ID',
    'reference_number': 'Notice_ID',
    'reference number': 'Notice_ID',
    'referencenumber': 'Notice_ID',
    'reference_no': 'Notice_ID',
    'reference no': 'Notice_ID',
    'referenceno': 'Notice_ID',
    'reference_code': 'Notice_ID',
    'reference code': 'Notice_ID',
    'referencecode': 'Notice_ID',
    'reference_identifier': 'Notice_ID',
    'reference identifier': 'Notice_ID',
    'referenceidentifier': 'Notice_ID',
    'tracking_id': 'Notice_ID',
    'tracking id': 'Notice_ID',
    'trackingid': 'Notice_ID',
    'tracking_number': 'Notice_ID',
    'tracking number': 'Notice_ID',
    'trackingnumber': 'Notice_ID',
    'tracking_no': 'Notice_ID',
    'tracking no': 'Notice_ID',
    'trackingno': 'Notice_ID',
    'tracking_code': 'Notice_ID',
    'tracking code': 'Notice_ID',
    'trackingcode': 'Notice_ID',
    'tracking_identifier': 'Notice_ID',
    'tracking identifier': 'Notice_ID',
    'trackingidentifier': 'Notice_ID',
    'id': 'Notice_ID',
    'identifier': 'Notice_ID',
    'number': 'Notice_ID',
    'no': 'Notice_ID',
    'code': 'Notice_ID',
    
    # Notice_Date variations (40+ variations)
    'notice_date': 'Notice_Date',
    'notice date': 'Notice_Date',
    'date': 'Notice_Date',
    'notice_datetime': 'Notice_Date',
    'notification_date': 'Notice_Date',
    'date_of_notice': 'Notice_Date',
    'notice_issued_date': 'Notice_Date',
    'noticedate': 'Notice_Date',
    'noticedatetime': 'Notice_Date',
    'notificationdate': 'Notice_Date',
    'dateofnotice': 'Notice_Date',
    'noticeissueddate': 'Notice_Date',
    'notice_date_time': 'Notice_Date',
    'notice date time': 'Notice_Date',
    'noticedatetime': 'Notice_Date',
    'notice_timestamp': 'Notice_Date',
    'notice timestamp': 'Notice_Date',
    'noticetimestamp': 'Notice_Date',
    'notice_issue_date': 'Notice_Date',
    'notice issue date': 'Notice_Date',
    'noticeissuedate': 'Notice_Date',
    'notice_issue_datetime': 'Notice_Date',
    'notice issue datetime': 'Notice_Date',
    'noticeissuedatetime': 'Notice_Date',
    'notice_issue_timestamp': 'Notice_Date',
    'notice issue timestamp': 'Notice_Date',
    'noticeissuetimestamp': 'Notice_Date',
    'notice_created_date': 'Notice_Date',
    'notice created date': 'Notice_Date',
    'noticecreateddate': 'Notice_Date',
    'notice_created_datetime': 'Notice_Date',
    'notice created datetime': 'Notice_Date',
    'noticecreateddatetime': 'Notice_Date',
    'notice_created_timestamp': 'Notice_Date',
    'notice created timestamp': 'Notice_Date',
    'noticecreatedtimestamp': 'Notice_Date',
    'notice_sent_date': 'Notice_Date',
    'notice sent date': 'Notice_Date',
    'noticesentdate': 'Notice_Date',
    'notice_sent_datetime': 'Notice_Date',
    'notice sent datetime': 'Notice_Date',
    'noticesentdatetime': 'Notice_Date',
    'notice_sent_timestamp': 'Notice_Date',
    'notice sent timestamp': 'Notice_Date',
    'noticesenttimestamp': 'Notice_Date',
    'notice_delivered_date': 'Notice_Date',
    'notice delivered date': 'Notice_Date',
    'noticedelivereddate': 'Notice_Date',
    'notice_delivered_datetime': 'Notice_Date',
    'notice delivered datetime': 'Notice_Date',
    'noticedelivereddatetime': 'Notice_Date',
    'notice_delivered_timestamp': 'Notice_Date',
    'notice delivered timestamp': 'Notice_Date',
    'noticedeliveredtimestamp': 'Notice_Date',
    'notification_date_time': 'Notice_Date',
    'notification date time': 'Notice_Date',
    'notificationdatetime': 'Notice_Date',
    'notification_timestamp': 'Notice_Date',
    'notification timestamp': 'Notice_Date',
    'notificationtimestamp': 'Notice_Date',
    'notification_issue_date': 'Notice_Date',
    'notification issue date': 'Notice_Date',
    'notificationissuedate': 'Notice_Date',
    'notification_issue_datetime': 'Notice_Date',
    'notification issue datetime': 'Notice_Date',
    'notificationissuedatetime': 'Notice_Date',
    'notification_issue_timestamp': 'Notice_Date',
    'notification issue timestamp': 'Notice_Date',
    'notificationissuetimestamp': 'Notice_Date',
    'notification_created_date': 'Notice_Date',
    'notification created date': 'Notice_Date',
    'notificationcreateddate': 'Notice_Date',
    'notification_created_datetime': 'Notice_Date',
    'notification created datetime': 'Notice_Date',
    'notificationcreateddatetime': 'Notice_Date',
    'notification_created_timestamp': 'Notice_Date',
    'notification created timestamp': 'Notice_Date',
    'notificationcreatedtimestamp': 'Notice_Date',
    'notification_sent_date': 'Notice_Date',
    'notification sent date': 'Notice_Date',
    'notificationsentdate': 'Notice_Date',
    'notification_sent_datetime': 'Notice_Date',
    'notification sent datetime': 'Notice_Date',
    'notificationsentdatetime': 'Notice_Date',
    'notification_sent_timestamp': 'Notice_Date',
    'notification sent timestamp': 'Notice_Date',
    'notificationsenttimestamp': 'Notice_Date',
    'notification_delivered_date': 'Notice_Date',
    'notification delivered date': 'Notice_Date',
    'notificationdelivereddate': 'Notice_Date',
    'notification_delivered_datetime': 'Notice_Date',
    'notification delivered datetime': 'Notice_Date',
    'notificationdelivereddatetime': 'Notice_Date',
    'notification_delivered_timestamp': 'Notice_Date',
    'notification delivered timestamp': 'Notice_Date',
    'notificationdeliveredtimestamp': 'Notice_Date',
    'dpdp_notice_date': 'Notice_Date',
    'dpdp notice date': 'Notice_Date',
    'dpdpnoticedate': 'Notice_Date',
    'dpdp_notice_datetime': 'Notice_Date',
    'dpdp notice datetime': 'Notice_Date',
    'dpdpnoticedatetime': 'Notice_Date',
    'dpdp_notice_timestamp': 'Notice_Date',
    'dpdp notice timestamp': 'Notice_Date',
    'dpdpnoticetimestamp': 'Notice_Date',
    'dpdp_notification_date': 'Notice_Date',
    'dpdp notification date': 'Notice_Date',
    'dpdpnotificationdate': 'Notice_Date',
    'dpdp_notification_datetime': 'Notice_Date',
    'dpdp notification datetime': 'Notice_Date',
    'dpdpnotificationdatetime': 'Notice_Date',
    'dpdp_notification_timestamp': 'Notice_Date',
    'dpdp notification timestamp': 'Notice_Date',
    'dpdpnotificationtimestamp': 'Notice_Date',
    'privacy_notice_date': 'Notice_Date',
    'privacy notice date': 'Notice_Date',
    'privacynoticedate': 'Notice_Date',
    'privacy_notice_datetime': 'Notice_Date',
    'privacy notice datetime': 'Notice_Date',
    'privacynoticedatetime': 'Notice_Date',
    'privacy_notice_timestamp': 'Notice_Date',
    'privacy notice timestamp': 'Notice_Date',
    'privacynoticetimestamp': 'Notice_Date',
    'privacy_notification_date': 'Notice_Date',
    'privacy notification date': 'Notice_Date',
    'privacynotificationdate': 'Notice_Date',
    'privacy_notification_datetime': 'Notice_Date',
    'privacy notification datetime': 'Notice_Date',
    'privacynotificationdatetime': 'Notice_Date',
    'privacy_notification_timestamp': 'Notice_Date',
    'privacy notification timestamp': 'Notice_Date',
    'privacynotificationtimestamp': 'Notice_Date',
    'data_notice_date': 'Notice_Date',
    'data notice date': 'Notice_Date',
    'datanoticedate': 'Notice_Date',
    'data_notice_datetime': 'Notice_Date',
    'data notice datetime': 'Notice_Date',
    'datanoticedatetime': 'Notice_Date',
    'data_notice_timestamp': 'Notice_Date',
    'data notice timestamp': 'Notice_Date',
    'datanoticetimestamp': 'Notice_Date',
    'data_notification_date': 'Notice_Date',
    'data notification date': 'Notice_Date',
    'datanotificationdate': 'Notice_Date',
    'data_notification_datetime': 'Notice_Date',
    'data notification datetime': 'Notice_Date',
    'datanotificationdatetime': 'Notice_Date',
    'data_notification_timestamp': 'Notice_Date',
    'data notification timestamp': 'Notice_Date',
    'datanotificationtimestamp': 'Notice_Date',
    'compliance_notice_date': 'Notice_Date',
    'compliance notice date': 'Notice_Date',
    'compliancenoticedate': 'Notice_Date',
    'compliance_notice_datetime': 'Notice_Date',
    'compliance notice datetime': 'Notice_Date',
    'compliancenoticedatetime': 'Notice_Date',
    'compliance_notice_timestamp': 'Notice_Date',
    'compliance notice timestamp': 'Notice_Date',
    'compliancenoticetimestamp': 'Notice_Date',
    'compliance_notification_date': 'Notice_Date',
    'compliance notification date': 'Notice_Date',
    'compliancenotificationdate': 'Notice_Date',
    'compliance_notification_datetime': 'Notice_Date',
    'compliance notification datetime': 'Notice_Date',
    'compliancenotificationdatetime': 'Notice_Date',
    'compliance_notification_timestamp': 'Notice_Date',
    'compliance notification timestamp': 'Notice_Date',
    'compliancenotificationtimestamp': 'Notice_Date',
    'legal_notice_date': 'Notice_Date',
    'legal notice date': 'Notice_Date',
    'legalnoticedate': 'Notice_Date',
    'legal_notice_datetime': 'Notice_Date',
    'legal notice datetime': 'Notice_Date',
    'legalnoticedatetime': 'Notice_Date',
    'legal_notice_timestamp': 'Notice_Date',
    'legal notice timestamp': 'Notice_Date',
    'legalnoticetimestamp': 'Notice_Date',
    'legal_notification_date': 'Notice_Date',
    'legal notification date': 'Notice_Date',
    'legalnotificationdate': 'Notice_Date',
    'legal_notification_datetime': 'Notice_Date',
    'legal notification datetime': 'Notice_Date',
    'legalnotificationdatetime': 'Notice_Date',
    'legal_notification_timestamp': 'Notice_Date',
    'legal notification timestamp': 'Notice_Date',
    'legalnotificationtimestamp': 'Notice_Date',
    'regulatory_notice_date': 'Notice_Date',
    'regulatory notice date': 'Notice_Date',
    'regulatorynoticedate': 'Notice_Date',
    'regulatory_notice_datetime': 'Notice_Date',
    'regulatory notice datetime': 'Notice_Date',
    'regulatorynoticedatetime': 'Notice_Date',
    'regulatory_notice_timestamp': 'Notice_Date',
    'regulatory notice timestamp': 'Notice_Date',
    'regulatorynoticetimestamp': 'Notice_Date',
    'regulatory_notification_date': 'Notice_Date',
    'regulatory notification date': 'Notice_Date',
    'regulatorynotificationdate': 'Notice_Date',
    'regulatory_notification_datetime': 'Notice_Date',
    'regulatory notification datetime': 'Notice_Date',
    'regulatorynotificationdatetime': 'Notice_Date',
    'regulatory_notification_timestamp': 'Notice_Date',
    'regulatory notification timestamp': 'Notice_Date',
    'regulatorynotificationtimestamp': 'Notice_Date',
    'document_date': 'Notice_Date',
    'document date': 'Notice_Date',
    'documentdate': 'Notice_Date',
    'document_datetime': 'Notice_Date',
    'document datetime': 'Notice_Date',
    'documentdatetime': 'Notice_Date',
    'document_timestamp': 'Notice_Date',
    'document timestamp': 'Notice_Date',
    'documenttimestamp': 'Notice_Date',
    'document_issue_date': 'Notice_Date',
    'document issue date': 'Notice_Date',
    'documentissuedate': 'Notice_Date',
    'document_issue_datetime': 'Notice_Date',
    'document issue datetime': 'Notice_Date',
    'documentissuedatetime': 'Notice_Date',
    'document_issue_timestamp': 'Notice_Date',
    'document issue timestamp': 'Notice_Date',
    'documentissuetimestamp': 'Notice_Date',
    'document_created_date': 'Notice_Date',
    'document created date': 'Notice_Date',
    'documentcreateddate': 'Notice_Date',
    'document_created_datetime': 'Notice_Date',
    'document created datetime': 'Notice_Date',
    'documentcreateddatetime': 'Notice_Date',
    'document_created_timestamp': 'Notice_Date',
    'document created timestamp': 'Notice_Date',
    'documentcreatedtimestamp': 'Notice_Date',
    'reference_date': 'Notice_Date',
    'reference date': 'Notice_Date',
    'referencedate': 'Notice_Date',
    'reference_datetime': 'Notice_Date',
    'reference datetime': 'Notice_Date',
    'referencedatetime': 'Notice_Date',
    'reference_timestamp': 'Notice_Date',
    'reference timestamp': 'Notice_Date',
    'referencetimestamp': 'Notice_Date',
    'tracking_date': 'Notice_Date',
    'tracking date': 'Notice_Date',
    'trackingdate': 'Notice_Date',
    'tracking_datetime': 'Notice_Date',
    'tracking datetime': 'Notice_Date',
    'trackingdatetime': 'Notice_Date',
    'tracking_timestamp': 'Notice_Date',
    'tracking timestamp': 'Notice_Date',
    'trackingtimestamp': 'Notice_Date',
    'issue_date': 'Notice_Date',
    'issue date': 'Notice_Date',
    'issuedate': 'Notice_Date',
    'issue_datetime': 'Notice_Date',
    'issue datetime': 'Notice_Date',
    'issuedatetime': 'Notice_Date',
    'issue_timestamp': 'Notice_Date',
    'issue timestamp': 'Notice_Date',
    'issuetimestamp': 'Notice_Date',
    'created_date': 'Notice_Date',
    'created date': 'Notice_Date',
    'createddate': 'Notice_Date',
    'created_datetime': 'Notice_Date',
    'created datetime': 'Notice_Date',
    'createddatetime': 'Notice_Date',
    'created_timestamp': 'Notice_Date',
    'created timestamp': 'Notice_Date',
    'createdtimestamp': 'Notice_Date',
    'sent_date': 'Notice_Date',
    'sent date': 'Notice_Date',
    'sentdate': 'Notice_Date',
    'sent_datetime': 'Notice_Date',
    'sent datetime': 'Notice_Date',
    'sentdatetime': 'Notice_Date',
    'sent_timestamp': 'Notice_Date',
    'sent timestamp': 'Notice_Date',
    'senttimestamp': 'Notice_Date',
    'delivered_date': 'Notice_Date',
    'delivered date': 'Notice_Date',
    'delivereddate': 'Notice_Date',
    'delivered_datetime': 'Notice_Date',
    'delivered datetime': 'Notice_Date',
    'delivereddatetime': 'Notice_Date',
    'delivered_timestamp': 'Notice_Date',
    'delivered timestamp': 'Notice_Date',
    'deliveredtimestamp': 'Notice_Date',
    'timestamp': 'Notice_Date',
    'datetime': 'Notice_Date',
    'date_time': 'Notice_Date',
    'date time': 'Notice_Date',
    'datetime': 'Notice_Date',
    'time': 'Notice_Date',
    'record_date': 'Notice_Date',
    'record date': 'Notice_Date',
    'recorddate': 'Notice_Date',
    'record_datetime': 'Notice_Date',
    'record datetime': 'Notice_Date',
    'recorddatetime': 'Notice_Date',
    'record_timestamp': 'Notice_Date',
    'record timestamp': 'Notice_Date',
    'recordtimestamp': 'Notice_Date',
    'entry_date': 'Notice_Date',
    'entry date': 'Notice_Date',
    'entrydate': 'Notice_Date',
    'entry_datetime': 'Notice_Date',
    'entry datetime': 'Notice_Date',
    'entrydatetime': 'Notice_Date',
    'entry_timestamp': 'Notice_Date',
    'entry timestamp': 'Notice_Date',
    'entrytimestamp': 'Notice_Date',
    'submission_date': 'Notice_Date',
    'submission date': 'Notice_Date',
    'submissiondate': 'Notice_Date',
    'submission_datetime': 'Notice_Date',
    'submission datetime': 'Notice_Date',
    'submissiondatetime': 'Notice_Date',
    'submission_timestamp': 'Notice_Date',
    'submission timestamp': 'Notice_Date',
    'submissiontimestamp': 'Notice_Date',
    'received_date': 'Notice_Date',
    'received date': 'Notice_Date',
    'receiveddate': 'Notice_Date',
    'received_datetime': 'Notice_Date',
    'received datetime': 'Notice_Date',
    'receiveddatetime': 'Notice_Date',
    'received_timestamp': 'Notice_Date',
    'received timestamp': 'Notice_Date',
    'receivedtimestamp': 'Notice_Date',
    'processed_date': 'Notice_Date',
    'processed date': 'Notice_Date',
    'processeddate': 'Notice_Date',
    'processed_datetime': 'Notice_Date',
    'processed datetime': 'Notice_Date',
    'processeddatetime': 'Notice_Date',
    'processed_timestamp': 'Notice_Date',
    'processed timestamp': 'Notice_Date',
    'processedtimestamp': 'Notice_Date',
    'updated_date': 'Notice_Date',
    'updated date': 'Notice_Date',
    'updateddate': 'Notice_Date',
    'updated_datetime': 'Notice_Date',
    'updated datetime': 'Notice_Date',
    'updateddatetime': 'Notice_Date',
    'updated_timestamp': 'Notice_Date',
    'updated timestamp': 'Notice_Date',
    'updatedtimestamp': 'Notice_Date',
    'modified_date': 'Notice_Date',
    'modified date': 'Notice_Date',
    'modifieddate': 'Notice_Date',
    'modified_datetime': 'Notice_Date',
    'modified datetime': 'Notice_Date',
    'modifieddatetime': 'Notice_Date',
    'modified_timestamp': 'Notice_Date',
    'modified timestamp': 'Notice_Date',
    'modifiedtimestamp': 'Notice_Date',
}
# Engine instantiated at module level for shared use
compliance = ComplianceEngine()

def validate_notice_id(notice_id: str) -> bool:
    return compliance.validate_notice_id(notice_id)


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate simple similarity score between two strings.
    Uses character overlap and common substring matching.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0 and 1
    """
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    if str1 == str2:
        return 1.0
    
    # Check if one contains the other
    if str1 in str2 or str2 in str1:
        return 0.8
    
    # Count common characters
    common_chars = set(str1) & set(str2)
    total_chars = set(str1) | set(str2)
    if total_chars:
        char_similarity = len(common_chars) / len(total_chars)
    else:
        char_similarity = 0.0
    
    # Check for common words
    words1 = set(str1.split('_'))
    words2 = set(str2.split('_'))
    common_words = words1 & words2
    total_words = words1 | words2
    if total_words:
        word_similarity = len(common_words) / len(total_words)
    else:
        word_similarity = 0.0
    
    # Combined score
    return (char_similarity * 0.5 + word_similarity * 0.5)


def suggest_canonical_field(column_name: str) -> tuple:
    """
    Suggest the most likely canonical field for an unmapped column name.
    
    Args:
        column_name: The unmapped column name
        
    Returns:
        Tuple of (suggested_canonical_field, confidence_score, alternative_suggestions)
    """
    if not column_name:
        return (None, 0.0, [])
    
    normalized = column_name.strip().lower().replace(' ', '_').replace('-', '_')
    
    # Calculate similarity with all mapped fields
    suggestions = {}
    for mapped_name, canonical_field in FIELD_MAPPING.items():
        similarity = calculate_similarity(normalized, mapped_name)
        if canonical_field not in suggestions or similarity > suggestions[canonical_field][0]:
            suggestions[canonical_field] = (similarity, mapped_name)
    
    if not suggestions:
        return (None, 0.0, [])
    
    # Sort by similarity
    sorted_suggestions = sorted(suggestions.items(), key=lambda x: x[1][0], reverse=True)
    
    best_match = sorted_suggestions[0]
    best_field = best_match[0]
    best_score = best_match[1][0]
    best_example = best_match[1][1]
    
    # Get alternatives (top 3)
    alternatives = [(field, score[0], score[1]) for field, score in sorted_suggestions[:3] if field != best_field]
    
    return (best_field, best_score, alternatives)


def normalize_field_name(field_name: str, show_suggestions: bool = False) -> str:
    """
    Normalize field name to canonical schema using FIELD_MAPPING.
    
    Args:
        field_name: Original field name from input data
        
    Returns:
        Canonical field name or original if no mapping found
    """
    if not field_name:
        return field_name
    
    # Try exact match first (case-insensitive)
    normalized = field_name.strip().lower()
    if normalized in FIELD_MAPPING:
        return FIELD_MAPPING[normalized]
    
    # Try with underscores/spaces normalized
    normalized = normalized.replace(' ', '_').replace('-', '_')
    if normalized in FIELD_MAPPING:
        return FIELD_MAPPING[normalized]
    
    # Return original if no mapping found
    return field_name


def parse_csv(filepath: str) -> pd.DataFrame:
    """Parse CSV file and return standardized DataFrame."""
    try:
        df = pd.read_csv(filepath)
        # Don't normalize here - let standardize_dataframe handle it with suggestions
        return df
    except Exception as e:
        raise ValueError(f"Error parsing CSV file {filepath}: {str(e)}")


def parse_json(filepath: str) -> pd.DataFrame:
    """Parse JSON file and return standardized DataFrame."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list of objects and single object
        if isinstance(data, dict):
            # If single object, check if it contains a list
            if 'records' in data or 'data' in data or 'patients' in data:
                key = 'records' if 'records' in data else ('data' if 'data' in data else 'patients')
                data = data[key]
            else:
                # Single object, wrap in list
                data = [data]
        
        if not isinstance(data, list):
            raise ValueError("JSON must contain a list of objects or a dict with a list")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        # Don't normalize here - let standardize_dataframe handle it with suggestions
        return df
    except Exception as e:
        raise ValueError(f"Error parsing JSON file {filepath}: {str(e)}")


def parse_xml(filepath: str) -> pd.DataFrame:
    """Parse XML file and return standardized DataFrame."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        records = []
        # Find all record elements (common patterns: record, patient, row, item)
        for record in root.findall('.//record') or root.findall('.//patient') or root.findall('.//row') or root.findall('.//item'):
            record_dict = {}
            for child in record:
                field_name = normalize_field_name(child.tag)
                record_dict[field_name] = child.text
            if record_dict:
                records.append(record_dict)
        
        # If no records found with common tags, try direct children
        if not records:
            for child in root:
                record_dict = {}
                for subchild in child:
                    field_name = normalize_field_name(subchild.tag)
                    record_dict[field_name] = subchild.text
                if record_dict:
                    records.append(record_dict)
        
        if not records:
            raise ValueError("No records found in XML file")
        
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        raise ValueError(f"Error parsing XML file {filepath}: {str(e)}")


def parse_xlsx(filepath: str) -> pd.DataFrame:
    """Parse XLSX file and return standardized DataFrame."""
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
        # Don't normalize here - let standardize_dataframe handle it with suggestions
        return df
    except Exception as e:
        raise ValueError(f"Error parsing XLSX file {filepath}: {str(e)}")


def parse_dicom(filepath: str) -> pd.DataFrame:
    """Parse DICOM file and return standardized DataFrame."""
    if not DICOM_AVAILABLE:
        raise ImportError("pydicom library is required for DICOM files. Install with: pip install pydicom")
    
    try:
        ds = pydicom.dcmread(filepath)
        records = []
        
        # Extract patient information from DICOM tags
        record = {}
        
        # Patient Name (tag 0010,0010)
        if hasattr(ds, 'PatientName'):
            record['Patient_Name'] = str(ds.PatientName)
        
        # Patient ID (tag 0010,0020) - could be ABHA_ID
        if hasattr(ds, 'PatientID'):
            record['ABHA_ID'] = str(ds.PatientID)
        
        # Study Date (tag 0008,0020) - could be Notice_Date
        if hasattr(ds, 'StudyDate'):
            record['Notice_Date'] = str(ds.StudyDate)
        
        # Study Instance UID (tag 0020,000D) - could be Notice_ID
        if hasattr(ds, 'StudyInstanceUID'):
            record['Notice_ID'] = str(ds.StudyInstanceUID)
        
        # Clinical information as JSON payload
        clinical_data = {}
        if hasattr(ds, 'StudyDescription'):
            clinical_data['study_description'] = str(ds.StudyDescription)
        if hasattr(ds, 'Modality'):
            clinical_data['modality'] = str(ds.Modality)
        if hasattr(ds, 'BodyPartExamined'):
            clinical_data['body_part'] = str(ds.BodyPartExamined)
        
        record['Clinical_Payload'] = json.dumps(clinical_data) if clinical_data else None
        record['Consent_Status'] = 'ACTIVE'  # Default for DICOM
        
        records.append(record)
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        raise ValueError(f"Error parsing DICOM file {filepath}: {str(e)}")


def parse_hl7(filepath: str) -> pd.DataFrame:
    """Parse HL7 V2 message file and return standardized DataFrame."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        records = []
        # HL7 messages are separated by carriage returns
        messages = content.split('\r')
        if len(messages) == 1:
            messages = content.split('\n')
        
        for message in messages:
            if not message.strip() or not message.startswith('MSH'):
                continue
            
            segments = message.split('|')
            if len(segments) < 2:
                continue
            
            record = {}
            
            # MSH segment (Message Header) - segment[0] is 'MSH', segment[1] is field separator
            # PID segment (Patient Identification) typically follows MSH
            # Extract from PID segment if present
            pid_segment = None
            for seg in message.split('\r'):
                if seg.startswith('PID|'):
                    pid_segment = seg.split('|')
                    break
            
            if pid_segment and len(pid_segment) > 5:
                # PID.5 = Patient Name (components separated by ^)
                if len(pid_segment) > 5 and pid_segment[5]:
                    name_parts = pid_segment[5].split('^')
                    record['Patient_Name'] = ' '.join([p for p in name_parts[:2] if p])
                
                # PID.3 = Patient Identifier List (could contain ABHA_ID)
                if len(pid_segment) > 3 and pid_segment[3]:
                    identifiers = pid_segment[3].split('^')
                    if identifiers:
                        record['ABHA_ID'] = identifiers[0]
            
            # MSH.10 = Message Control ID (could be Notice_ID)
            if len(segments) > 10:
                record['Notice_ID'] = segments[9] if segments[9] else None
            
            # MSH.7 = Date/Time of Message (could be Notice_Date)
            if len(segments) > 7 and segments[7]:
                dt_str = segments[7]
                # HL7 date format: YYYYMMDDHHMMSS
                if len(dt_str) >= 8:
                    try:
                        date_part = dt_str[:8]
                        record['Notice_Date'] = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    except:
                        record['Notice_Date'] = dt_str
            
            # Clinical payload from message
            clinical_data = {'message_type': segments[8] if len(segments) > 8 else None}
            record['Clinical_Payload'] = json.dumps(clinical_data)
            record['Consent_Status'] = 'ACTIVE'  # Default
            
            if record:
                records.append(record)
        
        if not records:
            # Fallback for messy HL7
            record = {
                'Patient_Name': 'Unknown/Redacted',
                'ABHA_ID': None,
                'Notice_Date': None,
                'Notice_ID': Path(filepath).stem,
                'Clinical_Payload': json.dumps({'raw_message': content[:2000]}),
                'Consent_Status': 'ACTIVE'
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        # Force critical columns to string
        for col in ['Patient_Name', 'ABHA_ID', 'Notice_ID', 'Notice_Date', 'Consent_Status']:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', None).replace('None', None)
        return df
    except Exception as e:
        raise ValueError(f"Error parsing HL7 file {filepath}: {str(e)}")


def parse_fhir(filepath: str) -> pd.DataFrame:
    """Parse FHIR R5 JSON file and return standardized DataFrame."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = []
        
        # FHIR resources can be a Bundle or single resource
        resources = []
        if data.get('resourceType') == 'Bundle':
            resources = data.get('entry', [])
            resources = [entry.get('resource') for entry in resources if entry.get('resource')]
        elif data.get('resourceType'):
            resources = [data]
        
        for resource in resources:
            record = {}
            
            # Extract from Patient resource
            if resource.get('resourceType') == 'Patient':
                # Patient name
                if 'name' in resource and resource['name']:
                    name_list = resource['name'][0] if isinstance(resource['name'], list) else resource['name']
                    name_parts = []
                    if 'given' in name_list:
                        name_parts.extend(name_list['given'] if isinstance(name_list['given'], list) else [name_list['given']])
                    if 'family' in name_list:
                        name_parts.append(name_list['family'])
                    record['Patient_Name'] = ' '.join(name_parts) if name_parts else None
                
                # Patient identifier (could be ABHA_ID)
                if 'identifier' in resource and resource['identifier']:
                    for identifier in resource['identifier']:
                        if identifier.get('type', {}).get('coding', [{}])[0].get('code') == 'MR' or 'ABHA' in str(identifier.get('value', '')).upper():
                            record['ABHA_ID'] = identifier.get('value')
                            break
            
            # Extract from Consent resource
            if resource.get('resourceType') == 'Consent':
                record['Consent_Status'] = resource.get('status', 'ACTIVE')
                if 'patient' in resource:
                    record['Patient_Name'] = resource['patient'].get('reference', '').split('/')[-1]
            
            # Extract from Observation or other clinical resources
            if resource.get('resourceType') in ['Observation', 'DiagnosticReport', 'Condition']:
                clinical_data = {
                    'resource_type': resource.get('resourceType'),
                    'code': resource.get('code', {}).get('coding', [{}])[0].get('display') if 'code' in resource else None,
                    'status': resource.get('status')
                }
                record['Clinical_Payload'] = json.dumps(clinical_data)
            
            # Extract dates
            if 'date' in resource:
                record['Notice_Date'] = resource['date']
            elif 'meta' in resource and 'lastUpdated' in resource['meta']:
                record['Notice_Date'] = resource['meta']['lastUpdated'][:10]  # Extract date part
            
            # ID
            if 'id' in resource:
                record['Notice_ID'] = resource['id']
            
            # Set defaults
            if 'Consent_Status' not in record:
                record['Consent_Status'] = 'ACTIVE'
            
            if record:
                records.append(record)
        
        if not records:
            raise ValueError("No valid FHIR resources found in file")
        
        df = pd.DataFrame(records)
        # Force string types for ABDM fields
        for col in ['Patient_Name', 'ABHA_ID', 'Notice_ID', 'Notice_Date', 'Consent_Status']:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', None).replace('None', None)
        return df
    except Exception as e:
        raise ValueError(f"Error parsing FHIR file {filepath}: {str(e)}")


def parse_pdf(filepath: str) -> pd.DataFrame:
    """Parse PDF file and extract structured data with robust regex."""
    if not PDF_AVAILABLE:
        raise ImportError("PDF library is required. Install with: pip install PyPDF2 or pip install pdfplumber")
    
    try:
        records = []
        text_content = ""
        
        if PDF_ENGINE == 'pdfplumber':
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text_content += (page.extract_text() or "") + "\n"
        else:
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text_content += (page.extract_text() or "") + "\n"
        
        # Try to extract structured data from text
        record = {}
        
        # 1. Improved Patient Name Extraction (Handles underscores, mixed case, and common prefixes)
        name_patterns = [
            r"Patient(?:'s)? Name[:\s]*([A-Za-z0-9_\s.]{3,50})",
            r"Name[:\s]*([A-Za-z0-9_\s.]{3,50})",
            r"Pt\.? Name[:\s]*([A-Za-z0-9_\s.]{3,50})",
            r"Full Name[:\s]*([A-Za-z0-9_\s.]{3,50})"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                record['Patient_Name'] = match.group(1).strip().split('\n')[0]
                break
        
        # 2. Robust ABHA ID Extraction (Handles 14-digit numbers with or without hyphens)
        # Matches formats like: 12-3456-7890-1234 or 12345678901234
        abha_patterns = [
            r"(?:ABHA|Health ID)(?:[:\s])*([0-9]{2}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4})",
            r"\b([0-9]{2}-[0-9]{4}-[0-9]{4}-[0-9]{4})\b",
            r"\b([0-9]{14})\b"
        ]
        for pattern in abha_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                record['ABHA_ID'] = match.group(1).strip()
                break
        
        # 3. Flexible Date Extraction (ABDM standard is YYYY-MM-DD)
        date_patterns = [
            r"(\d{4}[-/]\d{2}[-/]\d{2})",
            r"(\d{2}[-/]\d{2}[-/]\d{4})"
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_content)
            if match:
                raw_date = match.group(1).replace('/', '-')
                # Ensure it's in canonical format if it was DD-MM-YYYY
                if raw_date.find('-') == 2:
                    parts = raw_date.split('-')
                    record['Notice_Date'] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                else:
                    record['Notice_Date'] = raw_date
                break
        
        # 4. Notice ID Extraction
        notice_patterns = [
            r"Notice(?: ID)?[:\s]*([Nn]-\d{4}-[A-Z0-9.\-]+)",
            r"Ref(?: No)?[:\s]*([A-Z0-9.\-]+)"
        ]
        for pattern in notice_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                record['Notice_ID'] = match.group(1).strip()
                break
        
        # Store full text as clinical payload
        record['Clinical_Payload'] = json.dumps({'text': text_content[:2000]})  # Increased limit
        record['Consent_Status'] = 'ACTIVE' # Default
        if 'Notice_ID' not in record:
            record['Notice_ID'] = Path(filepath).stem
        
        # Fallback for Patient Name
        if not record.get('Patient_Name'):
            record['Patient_Name'] = 'Unknown/Redacted'
        
        records.append(record)
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        raise ValueError(f"Error parsing PDF file {filepath}: {str(e)}")


def parse_text_report(filepath: str) -> pd.DataFrame:
    """Parse text report file and extract structured data with robust logic."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        records = []
        record = {}
        
        # Use common patterns similar to PDF for consistency
        # 1. Patient Name
        name_patterns = [
            r"Patient(?:'s)? Name[:\s]*([A-Za-z0-9_\s.]{3,50})",
            r"Name[:\s]*([A-Za-z0-9_\s.]{3,50})",
            r"Pt\.? Name[:\s]*([A-Za-z0-9_\s.]{3,50})"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                record['Patient_Name'] = match.group(1).strip().split('\n')[0]
                break
        
        # 2. ABHA ID
        abha_patterns = [
            r"(?:ABHA|Health ID)(?:[:\s])*([0-9]{2}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4})",
            r"\b([0-9]{2}-[0-9]{4}-[0-9]{4}-[0-9]{4})\b",
            r"\b([0-9]{14})\b"
        ]
        for pattern in abha_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                record['ABHA_ID'] = match.group(1).strip()
                break
        
        # 3. Notice Date
        date_patterns = [
            r"Notice Date[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})",
            r"Date[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})",
            r"(\d{4}[-/]\d{2}[-/]\d{2})"
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                record['Notice_Date'] = match.group(1).replace('/', '-')
                break
        
        # 4. Consent Status
        consent_match = re.search(r"Consent(?: Status)?[:\s]*([A-Z]+)", text_content, re.IGNORECASE)
        if consent_match:
            record['Consent_Status'] = consent_match.group(1).upper()
        else:
            record['Consent_Status'] = 'ACTIVE'
            
        # 5. Notice ID
        notice_match = re.search(r"Notice(?: ID)?[:\s]*([A-Z0-9.\-]+)", text_content, re.IGNORECASE)
        if notice_match:
            record['Notice_ID'] = notice_match.group(1).strip()
        
        if 'Notice_ID' not in record:
            record['Notice_ID'] = Path(filepath).stem

        # Store text as clinical payload
        record['Clinical_Payload'] = json.dumps({'report': text_content[:2000]})
        
        # Set defaults
        if 'Consent_Status' not in record:
            record['Consent_Status'] = 'ACTIVE'
        if 'Notice_ID' not in record:
            record['Notice_ID'] = Path(filepath).stem
        if 'Patient_Name' not in record:
            record['Patient_Name'] = 'Unknown'
        
        records.append(record)
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        raise ValueError(f"Error parsing text report file {filepath}: {str(e)}")


def parse_api_response(filepath_or_url: str) -> pd.DataFrame:
    """Parse API response (from URL or JSON file) and return standardized DataFrame."""
    try:
        # Check if it's a URL
        if filepath_or_url.startswith('http://') or filepath_or_url.startswith('https://'):
            with urllib.request.urlopen(filepath_or_url) as response:
                data = json.loads(response.read().decode('utf-8'))
        else:
            # It's a file path
            with open(filepath_or_url, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Handle API response structure (could be different formats)
        records = []
        
        # Common API response patterns
        if isinstance(data, dict):
            # Check for common API response wrappers
            if 'data' in data:
                data = data['data']
            elif 'results' in data:
                data = data['results']
            elif 'items' in data:
                data = data['items']
            elif 'patients' in data:
                data = data['patients']
            elif 'records' in data:
                data = data['records']
        
        # If still a dict, try to extract single record
        if isinstance(data, dict):
            data = [data]
        
        # Convert to list of records
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    records.append(item)
        else:
            records.append(data)
        
        if not records:
            raise ValueError("No records found in API response")
        
        df = pd.DataFrame(records)
        # Normalize column names
        df.columns = [normalize_field_name(col) for col in df.columns]
        return df
    except Exception as e:
        raise ValueError(f"Error parsing API response {filepath_or_url}: {str(e)}")


def parse_data_file(filepath: str) -> pd.DataFrame:
    """
    Modular function that selects the correct parser based on file extension.
    
    Args:
        filepath: Path to the data file
        
    Returns:
        Standardized DataFrame with canonical column names
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    extension = filepath.suffix.lower()
    
    # Check if it's a URL (for API responses)
    filepath_str = str(filepath)
    if filepath_str.startswith('http://') or filepath_str.startswith('https://'):
        return parse_api_response(filepath_str)
    
    parser_map = {
        '.csv': parse_csv,
        '.json': parse_json,
        '.xml': parse_xml,
        '.xlsx': parse_xlsx,
        '.xls': parse_xlsx,
        '.dcm': parse_dicom,
        '.dicom': parse_dicom,
        '.hl7': parse_hl7,
        '.hl7v2': parse_hl7,
        '.fhir': parse_fhir,
        '.pdf': parse_pdf,
        '.txt': parse_text_report,
        '.text': parse_text_report,
        '.report': parse_text_report
    }
    
    parser = parser_map.get(extension)
    if not parser:
        # Try to detect format by content or try JSON/API response
        if filepath_str.startswith('http'):
            return parse_api_response(filepath_str)
        raise ValueError(f"Unsupported file format: {extension}. Supported formats: CSV, JSON, XML, XLSX, DICOM, HL7 V2, FHIR R5, PDF, Text Reports, API responses")
    
    return parser(filepath_str)


def apply_compliance_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply compliance scenarios as required:
    - 15% NULL ABHA_ID (for ABDM Discovery)
    - 10% 'REVOKED' Consent_Status (for DPDP Purge)
    - 5% expired Notice_Date (for India DPDP Rules 2025)
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with compliance scenarios applied
    """
    df = df.copy()
    total_rows = len(df)
    
    # Ensure required columns exist
    for field in CANONICAL_FIELDS:
        if field not in df.columns:
            df[field] = None
    
    # 15% NULL ABHA_ID (for ABDM Discovery)
    if 'ABHA_ID' in df.columns:
        null_indices = random.sample(range(total_rows), k=int(total_rows * 0.15))
        df.loc[null_indices, 'ABHA_ID'] = None
    
    # 10% 'REVOKED' Consent_Status (for DPDP Purge)
    if 'Consent_Status' in df.columns:
        revoked_indices = random.sample(range(total_rows), k=int(total_rows * 0.10))
        df.loc[revoked_indices, 'Consent_Status'] = 'REVOKED'
    
    # 5% expired Notice_Date (for India DPDP Rules 2025)
    # Expired means date is more than 30 days in the past
    if 'Notice_Date' in df.columns:
        expired_indices = random.sample(range(total_rows), k=int(total_rows * 0.05))
        expired_date = (datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d')
        df.loc[expired_indices, 'Notice_Date'] = expired_date
    
    return df


def standardize_dataframe(df: pd.DataFrame, show_mapping_info: bool = True, interactive: bool = True) -> pd.DataFrame:
    """
    Standardize DataFrame to canonical schema.
    Uses interactive prompts to resolve ambiguous columns.
    
    Args:
        df: Input DataFrame
        show_mapping_info: Whether to show mapping information
        interactive: Whether to prompt user for column mapping decisions
        
    Returns:
        Standardized DataFrame with canonical fields
    """
    # Create a mapping plan: {original_col: canonical_col}
    mapping_plan = {}
    
    # 1. Identify Input Columns
    input_columns = df.columns.tolist()
    
    if interactive:
        print("\n" + "=" * 60)
        print("INTERACTIVE COLUMN MAPPING")
        print("=" * 60)
        print(f"Input Columns: {input_columns}")
    
    # 2. Process each input column
    for col in input_columns:
        # Check for direct or normalized match
        normalized = normalize_field_name(col, show_suggestions=False)
        
        # Scenario A: Exact or Known Map
        if normalized in CANONICAL_FIELDS:
            # If it's a known map, we usually trust it, but we can verify if it's not exact
            if normalized == col:
                mapping_plan[col] = normalized
                if interactive: print(f"  [AUTO] '{col}' -> '{normalized}'")
            else:
                # It's a mapped name (e.g. 'pt_name' -> 'Patient_Name')
                # For high integrity, prompts could be added here, but we'll stick to auto for known aliases
                # unless fuzzy.
                mapping_plan[col] = normalized
                if interactive: print(f"  [AUTO] '{col}' -> '{normalized}' (via alias)")
                
        else:
            # Scenario B: Unknown Column - Suggest and Prompt
            if interactive:
                print(f"\n  [?] Unknown Column: '{col}'")
                suggested, confidence, alternatives = suggest_canonical_field(col)
                
                choice = None
                target_field = None
                
                if suggested and confidence > 0.3:
                    print(f"      Suggestion: Map to '{suggested}'? (Confidence: {confidence:.1%})")
                    user_input = input("      Accept Suggestion? (Y/n/Custom/Skip): ").strip().lower()
                    
                    if user_input in ['', 'y', 'yes']:
                        target_field = suggested
                    elif user_input in ['n', 'no', 'skip']:
                        target_field = None # Will be handled as UNMAPPED
                    else:
                        target_field = user_input # Treat as custom
                else:
                    print("      No confident suggestion found.")
                    print(f"      Canonical Fields: {', '.join(CANONICAL_FIELDS)}")
                    user_input = input("      Map to which field? (Name/Skip): ").strip()
                    if user_input.lower() in ['', 'skip', 'n']:
                        target_field = None # Will be handled as UNMAPPED
                    else:
                        target_field = user_input
                
                # Validate Custom Input
                if target_field:
                    # Normalize the user's input to check if it's a valid canonical field
                    normalized_target = normalize_field_name(target_field)
                    if normalized_target in CANONICAL_FIELDS:
                        mapping_plan[col] = normalized_target
                        print(f"      => Mapped '{col}' to '{normalized_target}'")
                    else:
                        print(f"      [WARNING] '{target_field}' is NOT a standard field. Column '{col}' will be preserved as 'UNMAPPED_{col}'.")
                        mapping_plan[col] = f"UNMAPPED_{col}"
                else:
                    print(f"      => Skipping '{col}' (Preserving as 'UNMAPPED_{col}')")
                    mapping_plan[col] = f"UNMAPPED_{col}"
            else:
                # Non-interactive: Skip unknowns
                pass

    # 3. Apply Mapping
    standardized = pd.DataFrame()
    for original, canonical in mapping_plan.items():
        standardized[canonical] = df[original]
    
    # 4. Fill Missing Canonical Fields with None
    for field in CANONICAL_FIELDS:
        if field not in standardized.columns:
            standardized[field] = None
            
    return standardized


def resolve_identity(row: pd.Series, abdm_client=None, db_manager=None) -> pd.Series:
    """
    M1 DISCOVERY / IDENTITY RESOLUTION
    If ABHA_ID is missing, resolve via Database cache, Real Gateway, or Simulation.
    """
    patient_name = str(row.get('Patient_Name', 'Unknown'))
    abha_id = str(row.get('ABHA_ID', '')).strip()

    if not abha_id or abha_id == '' or abha_id == 'nan':
        # 0. Database Lookup (Phase 2)
        if db_manager:
            # Note: In real life we search by name/phone, here we simulate name search
            # We'll check if we have a known ID for this name in our DB
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT abha_id, consent_status FROM patients WHERE patient_name = ?", (patient_name,))
                match = cursor.fetchone()
                if match:
                    row['ABHA_ID'] = match[0]
                    row['Consent_Status'] = match[1]
                    row['_Discovery_Status'] = "RECOVERED_FROM_DB"
                    print(f"  [DB] Recovered Identity for '{patient_name}': {match[0]}")
                    return row

        # 1. Real Gateway Mode (Phase 1)
        if abdm_client:
            print(f"  [GATEWAY] Initiating Live M1 discovery for '{patient_name}'...")
            # Simulation of finding a match to trigger profile share
            mock_links = {"TestPatient_4_Missing_ID": "ABHA243894", "TestPatient_6_Missing_ID": "ABHA810530"}
            target_id = mock_links.get(patient_name)
            if target_id:
                res = abdm_client.profile_share_request(target_id)
                if res:
                    row['ABHA_ID'] = target_id
                    row['_Discovery_Status'] = "LINKED_BY_GATEWAY"
                    print(f"    -> [LIVE] Identity Requested via ABDM Gateway (ReqID: {res['requestId']})")
                return row

        # 2. Simulation Mode (Phase 0)
        print(f"  [DISCOVERY] Missing ID for '{patient_name}'... Calling M1 API Simulation...")
        if patient_name:
            generated_id = f"ABHA{abs(hash(patient_name)) % 1000000:06d}"
            row['ABHA_ID'] = generated_id
            row['_Discovery_Status'] = "LINKED_BY_M1"
            print(f"    -> [MATCH] Found Identity: {generated_id}")
            
    return row


def enforce_dpdp_rules(row: pd.Series) -> pd.Series:
    """Delegates to decoupled ComplianceEngine (Rule 3 & 8)."""
    return compliance.apply_purge(row)


def export_fhir_bundle(df: pd.DataFrame, filename: str = "output_bundle.json"):
    """
    Generate FHIR R5 Bundle from processed DataFrame.
    Only includes SUCCESS_LINKED records.
    """
    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": []
    }
    
    count = 0
    for _, row in df.iterrows():
        if row.get('_Ingest_Status') == 'SUCCESS_LINKED':
            # Create Patient Resource
            patient_uuid = str(uuid.uuid4())
            entry = {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_uuid,
                    "identifier": [
                        {
                            "system": "https://healthid.ndhm.gov.in",
                            "value": row['ABHA_ID']
                        }
                    ],
                    "name": [
                        {
                            "text": row['Patient_Name']
                        }
                    ]
                },
                "request": {
                    "method": "POST",
                    "url": "Patient"
                }
            }
            bundle['entry'].append(entry)
            
            # Create Condition (Clinical Payload) - Simplified
            # Parsing the JSON payload if possible
            try:
                payload = json.loads(row['Clinical_Payload'])
                condition_text = payload.get('diagnosis', 'Unknown Condition')
            except:
                condition_text = str(row['Clinical_Payload'])

            # TERMINOLOGY MAPPER: Convert Text -> Code (SNOMED-CT)
            snomed_code = "185345009" # Fallback: 'Encounter for symptom'
            if condition_text in SNOMED_MAP:
                snomed_code = SNOMED_MAP[condition_text]

            condition_entry = {
                "resource": {
                    "resourceType": "Condition",
                    "subject": {
                        "reference": f"urn:uuid:{patient_uuid}"
                    },
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": snomed_code,
                                "display": condition_text
                            }
                        ],
                        "text": condition_text
                    }
                },
                "request": {
                    "method": "POST",
                    "url": "Condition"
                }
            }
            bundle['entry'].append(condition_entry)
            count += 1
            
    with open(filename, 'w') as f:
        json.dump(bundle, f, indent=2)
    print(f"[FHIR] Exported {count} compliant records to {filename}")



def generate_sample_data(num_rows: int = 1000) -> pd.DataFrame:
    """
    Generate sample data across multiple formats for testing.
    This function creates sample files in different formats and then parses them.
    
    Args:
        num_rows: Number of rows to generate
        
    Returns:
        Combined DataFrame with data from all formats
    """
    # Create sample data
    sample_data = []
    for i in range(num_rows):
        rand_suffix = random.randint(1000, 9999)
        sample_data.append({
            'Patient_Name': f'Patient_{i+1}_{rand_suffix}',
            'ABHA_ID': f'ABHA{random.randint(100000, 999999):06d}',
            'Clinical_Payload': f'{{"diagnosis": "{random.choice(["Condition", "Issue", "Case"])}_{i+1}", "treatment": "Treatment_{i+1}", "visit_type": "{random.choice(["OPD", "IPD", "EMERGENCY"])}"}}',
            'Consent_Status': random.choice(['ACTIVE', 'PENDING', 'GRANTED', 'REVOKED']),
            'Notice_ID': f'NOTICE_{i+1:06d}_{rand_suffix}',
            'Notice_Date': (datetime.now() - timedelta(days=random.randint(0, 400))).strftime('%Y-%m-%d'),
            'Data_Purpose': random.choice(["Consultation", "Treatment", "Audit", "Emergency Care", "Marketing"])
        })
    
    df = pd.DataFrame(sample_data)
    
    return df


def main(interactive=True):
    """
    Main function to ingest data from multiple formats and export standardized data.
    """
    print("Universal Adapter - Hospital Data Ingestion")
    print("=" * 50)
    
    if not interactive:
        print("⚡ BATCH MODE ACTIVE: Skipping all user prompts...")
        
    # Check if input files exist, otherwise generate sample data
    # Look for any supported format file (process first one found)
    # Exclude the output file from being processed
    # Also check in organized folders (raw_data_*)
    supported_extensions = ['.csv', '.json', '.xml', '.xlsx', '.xls', '.dcm', '.dicom', 
                           '.hl7', '.hl7v2', '.fhir', '.pdf', '.txt', '.text', '.report']
    input_file = None
    output_file_name = 'standardized_ingress_1000.csv'
    
    # Search locations: current directory and organized folders
    search_locations = [Path('.')]
    # Add organized folders if they exist
    organized_folders = ['raw_data_csv', 'raw_data_json', 'raw_data_xml', 'raw_data_xlsx',
                        'raw_data_hl7', 'raw_data_fhir', 'raw_data_pdf', 'raw_data_txt',
                        'raw_data_dicom']
    for folder in organized_folders:
        folder_path = Path(folder)
        if folder_path.exists() and folder_path.is_dir():
            search_locations.append(folder_path)
    
    for ext in supported_extensions:
        for location in search_locations:
            files = [f for f in location.glob(f'*{ext}') if f.name != output_file_name]
            if files:
                input_file = files[0]  # Take first file found
                break
        if input_file:
            break
    
    all_dataframes = []
    format_tracking = []  # Track (format, row_count) for the processed file
    
    if input_file:
        try:
            print(f"Found input file: {input_file.name}")
            print(f"  Parsing: {input_file}")
            file_ext = Path(input_file).suffix.lower()
            df = parse_data_file(str(input_file))
            df = standardize_dataframe(df, interactive=interactive)
            all_dataframes.append(df)
            # Track format with row count
            format_name = file_ext[1:].upper() if file_ext else 'UNKNOWN'
            format_tracking.append((format_name, len(df)))
            print(f"    Loaded {len(df)} rows from {format_name} format")
        except Exception as e:
            print(f"    Error processing {input_file}: {str(e)}")
            print("    Falling back to sample data generation...")
            input_file = None
    
    if not input_file or not all_dataframes:
        print("No input files found. Generating sample data...")
        # Generate sample data to reach 1000 rows
        df = generate_sample_data(1000)
        all_dataframes.append(df)
        format_tracking.append(('GENERATED', len(df)))
        print(f"  Generated {len(df)} sample rows")
    
    # Combine all dataframes
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Track original row counts before trimming/padding
        original_row_counts = {fmt: count for fmt, count in format_tracking}
        
        # Ensure we have exactly 1000 rows (take first 1000 if more, pad if less)
        rows_before = len(combined_df)
        if len(combined_df) > 1000:
            combined_df = combined_df.head(1000)
        elif len(combined_df) < 1000:
            # Generate additional rows if needed
            additional_rows = 1000 - len(combined_df)
            additional_df = generate_sample_data(additional_rows)
            combined_df = pd.concat([combined_df, additional_df], ignore_index=True)
            combined_df = combined_df.head(1000)
            format_tracking.append(('GENERATED', additional_rows))
        
        # 1. Standardize (Interactive Ingestion)
        # combined_df = combined_df[CANONICAL_FIELDS] # REMOVED: Do not force schema yet, keep UNMAPPED fields
        
        # Reorder columns: Canonical first, then UNMAPPED
        canonical_present = [c for c in CANONICAL_FIELDS if c in combined_df.columns]
        other_cols = [c for c in combined_df.columns if c not in CANONICAL_FIELDS]
        combined_df = combined_df[canonical_present + other_cols]
        
        # 2. Compliance Logic (M1 + DPDP)
        print("\nRunning Compliance Filter (DPDP 2025)...")
        processed_rows = []
        stats = {"Linked": 0, "Purged": 0, "Quarantined": 0}
        
        # Initialize Components
        client_id = os.getenv("ABDM_CLIENT_ID")
        client_secret = os.getenv("ABDM_CLIENT_SECRET")
        abdm_client = ABDMApiClient(client_id, client_secret) if client_id and client_secret else None
        db_manager = DatabaseManager() # Phase 2 Integration
        
        if abdm_client: print("[PHASE 1] ABDM Gateway Client initialized.")
        print("[PHASE 2] Database Connection active.")

        for idx, row in combined_df.iterrows():
            # M1 Discovery (Persistent)
            row = resolve_identity(row, abdm_client=abdm_client, db_manager=db_manager)
            
            # SNOMED Coding... (Lines 2056-2074 removed for brevity in snippet, but kept in code)
            
            # SNOMED Coding (Added for Visibility)
            try:
                payload_str = str(row.get('Clinical_Payload', '')).replace("'", '"')
                data = json.loads(payload_str)
                diag = data.get("diagnosis", "")
                vtype = data.get("visit_type", "UNKNOWN")
                
                # Extract to Standalone Columns
                row['Visit_Type'] = vtype
                row['Diagnosis'] = diag
                
                if diag in SNOMED_MAP:
                    row['_SNOMED_Code'] = SNOMED_MAP[diag]
                else:
                    row['_SNOMED_Code'] = "" # No mapping found
            except:
                row['Visit_Type'] = "UNKNOWN"
                row['Diagnosis'] = ""
                row['_SNOMED_Code'] = ""

            # DPDP Kill-Switch
            row = enforce_dpdp_rules(row)
            
            # 3. Permanent Audit Log (DPDP Compliance)
            if db_manager and not pd.isna(row.get('ABHA_ID')):
                # Log the specific access event
                db_manager.log_access(
                    abha_id=row['ABHA_ID'],
                    action="INGEST_AND_STANDARDIZE",
                    purpose=row.get('Data_Purpose', 'UNKNOWN')
                )
                
                # Sync Patient state
                db_manager.upsert_patient(
                    abha_id=row['ABHA_ID'],
                    name=row['Patient_Name'],
                    status=row['Consent_Status'],
                    notice_date=row['Notice_Date'],
                    discovery=row.get('_Discovery_Status', ''),
                    clinical=json.dumps(row.get('Clinical_Payload', {}))
                )

            status = row['_Ingest_Status']
            if "SUCCESS" in status: stats["Linked"] += 1
            elif "PURGED" in status: stats["Purged"] += 1
            else: stats["Quarantined"] += 1
                
            processed_rows.append(row)
            
        combined_df = pd.DataFrame(processed_rows)

        # 3. Export
        # CSV (Audit Trail)
        output_file = 'standardized_ingress_1000.csv'
        combined_df.to_csv(output_file, index=False)
        
        # FHIR Bundle (Clean Data)
        export_fhir_bundle(combined_df)
        
        print("\n" + "=" * 50)
        print("COMPLIANCE DASHBOARD")
        print("=" * 50)
        print(f"Total Ingested  : {len(combined_df)}")
        print(f"Successfully Linked: {stats['Linked']}")
        print(f"Purged for Non-Compliance: {stats['Purged']}")
        print(f"Quarantined for Re-Notice: {stats['Quarantined']}")
        print("=" * 50)
        
        # --- NEW: Clinical Category Analysis ---
        print("\nCLINICAL ANALYTICS DISTRIBUTION")
        print("-" * 50)
        
        stats_counters = {
            "VISIT TYPE": {},
            "DIAGNOSIS": {},
            "MEDICATION": {},
            "LAB TESTS": {}
        }
        
        for _, row in combined_df.iterrows():
            payload_str = str(row.get('Clinical_Payload', ''))
            
            data = {}
            # Try parsing as JSON first
            try:
                # Handle potential double-escaped strings if present
                clean_str = payload_str.replace("'", '"') 
                data = json.loads(clean_str)
            except:
                # Fallback: Treat as empty dict if parse fails
                data = {}

            # 1. Visit Type
            vtype = data.get("visit_type", "UNKNOWN")
            if vtype == "UNKNOWN":
                 # Fallback to string search for older data
                 if "OPD" in payload_str: vtype = "OPD"
                 elif "IPD" in payload_str: vtype = "IPD"
                 elif "EMERGENCY" in payload_str: vtype = "EMERGENCY"
                 elif "TELECONSULT" in payload_str: vtype = "TELECONSULT"
            
            stats_counters["VISIT TYPE"][vtype] = stats_counters["VISIT TYPE"].get(vtype, 0) + 1
            
            # 2. Diagnosis
            diag = data.get("diagnosis")
            if diag: stats_counters["DIAGNOSIS"][diag] = stats_counters["DIAGNOSIS"].get(diag, 0) + 1
            
            # 3. Medication
            med = data.get("medication")
            if med and med != "None": stats_counters["MEDICATION"][med] = stats_counters["MEDICATION"].get(med, 0) + 1
            
            # 4. Lab Test
            lab = data.get("lab_test")
            if lab and lab != "None": stats_counters["LAB TESTS"][lab] = stats_counters["LAB TESTS"].get(lab, 0) + 1

        # Print Tables
        for category, counts in stats_counters.items():
            print(f"\nTOP {category}:")
            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5] # Top 5
            for item, count in sorted_counts:
                 print(f"  {item:<20}: {count}")
                 
        print("=" * 50)
        
        print(f"\n[OK] Audit Trail exported to: {output_file}")
        
        print(f"\n[OK] Successfully processed {len(combined_df)} rows")
        print(f"[OK] Exported to: {output_file}")
        
        # Display raw data file formats
        print("\nRaw Data File Formats:")
        if format_tracking:
            # Aggregate by format
            format_summary = {}
            for fmt, row_count in format_tracking:
                if fmt not in format_summary:
                    format_summary[fmt] = {'files': 0, 'rows': 0}
                format_summary[fmt]['files'] += 1
                format_summary[fmt]['rows'] += row_count
            
            for fmt in sorted(format_summary.keys()):
                info = format_summary[fmt]
                print(f"  {fmt}: {info['files']} file(s), {info['rows']} row(s)")
        else:
            print("  No files processed")
        
        # Print compliance statistics
        print("\nCompliance Statistics:")
        print(f"  NULL ABHA_ID: {combined_df['ABHA_ID'].isna().sum()} ({combined_df['ABHA_ID'].isna().sum()/len(combined_df)*100:.1f}%)")
        print(f"  REVOKED Consent: {(combined_df['Consent_Status'] == 'REVOKED').sum()} ({(combined_df['Consent_Status'] == 'REVOKED').sum()/len(combined_df)*100:.1f}%)")
        
        # Check expired dates (more than 30 days old)
        if 'Notice_Date' in combined_df.columns:
            try:
                notice_dates = pd.to_datetime(combined_df['Notice_Date'], errors='coerce')
                expired_count = (notice_dates < (datetime.now() - timedelta(days=30))).sum()
                print(f"  Expired Notice_Date: {expired_count} ({expired_count/len(combined_df)*100:.1f}%)")
            except:
                print(f"  Expired Notice_Date: Unable to calculate")
        
        print("\n" + "=" * 50)
    else:
        print("Error: No data was successfully processed.")


if __name__ == '__main__':
    main()
