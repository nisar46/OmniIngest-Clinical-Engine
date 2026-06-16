"""
Script to create sample raw data files in all supported formats
"""

import pandas as pd
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random

def main(num_rows=1000, formats=None):
    if formats is None or len(formats) == 0:
        formats = ["CSV"]
        
    sample_data = []

    for i in range(num_rows):
        rand_suffix = random.randint(1000, 9999)
        
        # 80/20 Algorithmic Split
        rand_val = random.random()
        
        # Randomly use 2025 Notice IDs for Outdated Error (5% chance)
        year = 2026 if random.random() >= 0.05 else 2025
        notice_id = f"N-{year}-CONS-v1.{random.randint(0,9)}-{rand_suffix}-{i}"
        notice_date = (datetime.now() - timedelta(days=random.randint(0, 450))).strftime('%Y-%m-%d')
        data_purpose = random.choice(["Consultation", "Treatment", "Audit", "Emergency Care"])
        
        if rand_val < 0.80:
            # 80% Clean Pass: flawless, verified patient records
            abha_id = f"{random.randint(10, 99)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
            diag = random.choice(["Hypertension", "Diabetes", "Asthma", "Fever"])
            payload = f'{{"diagnosis": "{diag}", "treatment": "Prescribed rest", "visit_type": "OPD"}}'
            bill_amount = round(random.uniform(500, 2000), 2)
            consent_status = "ACTIVE"
        else:
            # 20% Polluted Target: comprehensive mixed blend
            pollution_type = random.random()
            
            # Base valid struct for mutations
            abha_id = f"{random.randint(10, 99)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
            payload = "Standard clinical examination."
            bill_amount = round(random.uniform(500, 2000), 2)
            consent_status = "ACTIVE"
            
            if pollution_type < 0.25:
                # Malformed ABHA ID
                abha_id = f"ABHA-{random.randint(100, 999)}"
            elif pollution_type < 0.50:
                # Missing ABHA ID
                abha_id = None
            elif pollution_type < 0.75:
                # Billing discrepancy (High bill, missing diagnosis)
                payload = "XYZ-LOG: No clinical notes available, unknown condition."
                bill_amount = round(random.uniform(3000, 8000), 2)
            else:
                # Consent revoked
                consent_status = "REVOKED"
            
        sample_data.append({
            'patient_name': f'Patient_{i+1}_{rand_suffix}',
            'abha_id': abha_id,
            'clinical_payload': payload,
            'bill_amount': bill_amount,
            'consent_status': consent_status,
            'notice_id': notice_id,
            'notice_date': notice_date,
            'data_purpose': data_purpose
        })

    print(f"Creating sample data files in formats: {formats}")

    if "CSV" in formats:
        df = pd.DataFrame(sample_data)
        df.to_csv('raw_data.csv', index=False)
        print("[OK] Created raw_data.csv")
        
    if "JSON" in formats:
        with open('raw_data.json', 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)
        print("[OK] Created raw_data.json")

    if "XML" in formats:
        root = ET.Element('patients')
        for record in sample_data:
            patient = ET.SubElement(root, 'patient')
            for key, value in record.items():
                elem = ET.SubElement(patient, key)
                elem.text = str(value)
        tree = ET.ElementTree(root)
        tree.write('raw_data.xml', encoding='utf-8', xml_declaration=True)
        print("[OK] Created raw_data.xml")

    if "XLSX" in formats:
        df = pd.DataFrame(sample_data)
        df.to_excel('raw_data.xlsx', index=False, engine='openpyxl')
        print("[OK] Created raw_data.xlsx")
        
    if "PDF" in formats:
        with open('raw_data_pdf.txt', 'w', encoding='utf-8') as f:
            for record in sample_data:
                f.write(f"Patient Name: {record['patient_name']}\n")
                f.write(f"ABHA ID: {record['abha_id']}\n")
                f.write(f"Notice ID: {record['notice_id']}\n")
                f.write(f"Notice Date: {record['notice_date']}\n")
                f.write(f"Consent Status: {record['consent_status']}\n")
                f.write(f"Bill Amount: {record['bill_amount']}\n")
                f.write(f"Clinical Payload: {record['clinical_payload']}\n")
                f.write("-" * 50 + "\n")
                
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            c = canvas.Canvas('raw_data.pdf', pagesize=letter)
            y = 750
            c.setFont("Helvetica", 10)
            for i, record in enumerate(sample_data):
                if y < 150:
                    c.showPage()
                    y = 750
                c.drawString(50, y, f"Patient Name: {record['patient_name']}")
                y -= 15
                c.drawString(50, y, f"ABHA ID: {record['abha_id']}")
                y -= 15
                c.drawString(50, y, f"Notice ID: {record['notice_id']}")
                y -= 15
                c.drawString(50, y, f"Notice Date: {record['notice_date']}")
                y -= 15
                c.drawString(50, y, f"Bill Amount: {record['bill_amount']}")
                y -= 15
                c.drawString(50, y, f"Consent Status: {record['consent_status']}")
                y -= 15
                c.drawString(50, y, f"Clinical Payload: {record['clinical_payload']}")
                y -= 15
                c.drawString(50, y, "==================================================")
                y -= 15
            c.save()
            print("[OK] Created raw_data.pdf")
        except ImportError:
            import shutil
            shutil.copy('raw_data_pdf.txt', 'raw_data.pdf')
            print("[OK] Created raw_data.pdf (via txt fallback)")

    if "TXT" in formats:
        with open('raw_data.txt', 'w', encoding='utf-8') as f:
            for record in sample_data:
                f.write(f"Patient Name: {record['patient_name']}\n")
                f.write(f"ABHA ID: {record['abha_id']}\n")
                f.write(f"Notice ID: {record['notice_id']}\n")
                f.write(f"Notice Date: {record['notice_date']}\n")
                f.write(f"Bill Amount: {record['bill_amount']}\n")
                f.write(f"Consent Status: {record['consent_status']}\n")
                f.write(f"Clinical Payload: {record['clinical_payload']}\n")
                f.write("=" * 50 + "\n")
        print("[OK] Created raw_data.txt")

    print("\n[OK] Requested sample data files created successfully!")

if __name__ == '__main__':
    main()
