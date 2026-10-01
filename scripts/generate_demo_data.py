import os
from pathlib import Path

def generate_demo_data():
    base_dir = Path("C:/Users/anshu/.gemini/antigravity/scratch/medgraph/data/demo")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    docs = {
        "2024-01-15_consultation.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
DOB: 1985-03-15
Gender: Female
MRN: MG-2024-001

Date: 2024-01-15
Doctor: Dr. Rajesh Patel
Type: Initial consultation

Patient presents with fatigue and weight gain.
Family history: Type 2 diabetes
Prescribed: Metformin 500mg twice daily
Recommended: HbA1c test, fasting glucose
Follow-up in 3 months
Allergy: Penicillin
""",
        "2024-01-20_prescription.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2024-01-20
Prescription:
- Metformin 500mg
- Twice daily
- 90 days supply
""",
        "2024-02-05_lab_report.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2024-02-05
Lab Results:
- HbA1c: 6.1%
- Fasting glucose: 108 mg/dL
- Total cholesterol: 210 mg/dL
- Triglycerides: 165 mg/dL
""",
        "2024-04-15_consultation.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2024-04-15
Doctor: Dr. Rajesh Patel
Type: Follow-up consultation

Lab results reviewed.
Metformin continued.
Recommended: repeat HbA1c in 6 months
Follow-up in 6 months
Allergy: Penicillin confirmed
""",
        "2024-10-20_lab_report.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2024-10-20
Lab Results:
- HbA1c: 6.5%
- Fasting glucose: 118 mg/dL
- Total cholesterol: 220 mg/dL
""",
        "2025-01-10_consultation.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2025-01-10
Doctor: Dr. Anita Sharma
Type: Consultation

HbA1c increasing.
Metformin dosage increased to 1000mg.
Added: Atorvastatin 10mg for cholesterol.
Recommended: cardiac risk assessment.
Follow-up in 3 months.
Allergies: No known drug allergies
""",
        "2025-03-15_lab_report.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2025-03-15
Lab Results:
- HbA1c: 6.8%
- Fasting glucose: 125 mg/dL
- LDL: 145 mg/dL
""",
        "2025-04-20_consultation.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2025-04-20
Doctor: Dr. Anita Sharma
Type: Follow-up

HbA1c still rising despite Metformin increase.
Metformin DISCONTINUED.
Started: Sitagliptin 100mg once daily.
Atorvastatin continued.
MRI recommended for reported knee pain.
Follow-up in 3 months.
""",
        "2025-05-10_discharge_summary.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2025-05-10
Type: Hospital visit / Discharge Summary

ER visit for hypoglycemic episode.
Sitagliptin adjusted.
Discharged same day.
Follow-up with endocrinologist recommended.
""",
        "2025-07-15_lab_report.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2025-07-15
Lab Results:
- HbA1c: 7.1%
- Fasting glucose: 132 mg/dL
""",
        "2025-08-01_referral.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2025-08-01
Type: Referral

Referred to Dr. Vikram Mehta, Endocrinology.
Reason: Suboptimal glycemic control.
""",
        "2026-01-20_consultation.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2026-01-20
Doctor: Dr. Vikram Mehta
Type: Endocrinology consultation

Review of diabetes management.
Sitagliptin continued.
Current Medication List includes: Metformin 1000mg.
MRI recommended (knee + spine).
Follow-up in 6 months.
""",
        "2026-03-10_mri_report.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2026-03-10
Type: MRI Report

Knee MRI.
Mild osteoarthritis.
No acute findings.
""",
        "2026-04-15_lab_report.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2026-04-15
Lab Results:
- HbA1c: 7.8%
- Fasting glucose: 142 mg/dL
- LDL: 128 mg/dL
""",
        "2026-06-01_medication_list.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2026-06-01
Type: Current medication list

- Metformin 1000mg (ACTIVE)
- Sitagliptin 100mg
- Atorvastatin 10mg
- Paracetamol PRN
""",
        "2026-07-20_unrelated.txt": """SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT
Patient: Sarah Chen
MRN: MG-2024-001

Date: 2026-07-20
Type: Dental check-up

No dental issues.
Routine cleaning.
"""
    }
    
    for filename, content in docs.items():
        with open(base_dir / filename, "w") as f:
            f.write(content)
            
    print(f"Generated {len(docs)} documents in {base_dir}")

if __name__ == "__main__":
    generate_demo_data()
