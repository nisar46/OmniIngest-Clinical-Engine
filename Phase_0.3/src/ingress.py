import polars as pl
import sqlite3
import os
import json
from thefuzz import process

# --- PILLAR 1: ARCHITECTURAL CONFIG ---
VALID_PILLARS = ["Patients", "Providers", "Visits", "Medications", "LabResults", "Insurance", "Ingress_Logs"]
KB_PATH = 'schema_kb.json'
DB_PATH = 'omniingest.db'

def load_brain():
    with open(KB_PATH, 'r') as f:
        return json.load(f)

def save_brain(mappings, pillar_map):
    with open(KB_PATH, 'w') as f:
        json.dump({"mappings": mappings, "pillar_map": pillar_map}, f, indent=4)

# --- PILLAR 2: THE COMMAND CENTER ENGINE ---
def run_ingress(file_path):
    # 1. LOAD MEMORY
    brain = load_brain()
    # Handle the case where JSON might be empty or in old format
    mappings = brain.get("mappings", {})
    pillar_map = brain.get("pillar_map", {})

    # 2. ARCHITECT'S DOMAIN HINT
    print(f"\n🌿 ACTIVE PILLARS: {VALID_PILLARS}")
    primary_focus = input("👉 ARCHITECT: What is the PRIMARY PILLAR for this file? ").strip()

    df_raw = pl.read_csv(file_path)
    actual_mapping = {}
    new_learnings = []

    print(f"\n" + "█"*85)
    print(f" ARCHITECT'S COMMAND CENTER | {os.path.basename(file_path)}")
    print("█"*85)

    for col in df_raw.columns:
        best_canonical, highest_score = None, 0
        
        # Search existing knowledge
        for canonical, synonyms in mappings.items():
            match, score = process.extractOne(col, synonyms) if synonyms else (None, 0)
            
            # Boost score if it belongs to the primary focus pillar
            if pillar_map.get(canonical) == primary_focus:
                score += 15
                
            if score > highest_score:
                highest_score, best_canonical = score, canonical

        # 3. THE INTERVIEW (For Unknowns or Weak Matches)
        if highest_score < 95:
            print(f"\n❓ UNKNOWN DATA: '{col}'")
            canonical_name = input(f"   1. What is the standard name for '{col}'? ").strip()
            print(f"   2. Valid Pillars: {VALID_PILLARS}")
            pillar_choice = input(f"      Attach to which Pillar? ").strip()

            if pillar_choice in VALID_PILLARS:
                # Update Brain
                if canonical_name not in mappings: mappings[canonical_name] = []
                if col not in mappings[canonical_name]: mappings[canonical_name].append(col)
                pillar_map[canonical_name] = pillar_choice
                save_brain(mappings, pillar_map)
                
                actual_mapping[col] = canonical_name
                new_learnings.append(f"'{col}' -> {canonical_name} ({pillar_choice})")
            else:
                print(f"   🚫 Invalid Pillar. Skipping '{col}'.")
        else:
            actual_mapping[col] = best_canonical
            print(f"{col:<25} | FUZZY    | {str(min(highest_score, 100))+'%':<8} | {best_canonical} ({pillar_map.get(best_canonical)})")

    print("\n" + "="*85)
    print(f" ✅ SUCCESS: {len(new_learnings)} New Branches Learned.")
    print("="*85 + "\n")

    return df_raw.rename({k: v for k, v in actual_mapping.items() if k in df_raw.columns})
