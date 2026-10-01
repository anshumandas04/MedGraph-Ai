"""
MedGraph Database Seeder
Creates demo users, patient, documents, events, medications, investigations, and signals.
Idempotent — skips if data already exists.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.user import User
from app.db.models.patient import Patient, PatientAccess
from app.db.models.document import Document, DocumentPage
from app.db.models.event import HealthEvent, EventAttribute, EventRelationship
from app.db.models.medication import Medication, MedicationEvent
from app.db.models.investigation import Investigation, InvestigationEvent
from app.db.models.signal import Signal, SignalEvidence
from app.db.models.search import SearchChunk
from app.db.models.audit import AuditLog, Feedback, DocumentProcessingJob
from app.core.config import settings
from app.core.security import hash_password


# ── Document content templates ──────────────────────────────────────────────

DOCUMENTS = [
    {
        "filename": "2024-01-15_consultation.txt",
        "date": date(2024, 1, 15),
        "type": "CONSULTATION",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Consultation Note\n"
            "Date: 15 January 2024\n"
            "Doctor: Dr. Rajesh Patel\n"
            "Patient: Sarah Chen (DOB: 15/03/1985)\n\n"
            "Presenting complaints: Fatigue and weight gain over past 3 months.\n"
            "Family history: Father — Type 2 Diabetes.\n\n"
            "Examination: BMI 28.5, BP 130/85 mmHg.\n\n"
            "Assessment: Pre-diabetic indicators. Elevated BMI.\n\n"
            "Plan:\n"
            "- Start Metformin 500mg twice daily\n"
            "- Order HbA1c and fasting glucose\n"
            "- Follow-up in 3 months\n\n"
            "Allergies: Penicillin\n"
        ),
    },
    {
        "filename": "2024-01-20_prescription.txt",
        "date": date(2024, 1, 20),
        "type": "PRESCRIPTION",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Prescription\n"
            "Date: 20 January 2024\n"
            "Doctor: Dr. Rajesh Patel\n"
            "Patient: Sarah Chen\n\n"
            "Metformin 500mg — twice daily — 90 days supply\n"
        ),
    },
    {
        "filename": "2024-02-05_lab_report.txt",
        "date": date(2024, 2, 5),
        "type": "LAB_REPORT",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Laboratory Report\n"
            "Date: 05 February 2024\n"
            "Patient: Sarah Chen\n\n"
            "HbA1c: 6.1% (Reference: <5.7 normal, 5.7-6.4 pre-diabetes)\n"
            "Fasting Glucose: 108 mg/dL (Reference: 70-100 normal)\n"
            "Total Cholesterol: 210 mg/dL\n"
            "Triglycerides: 165 mg/dL\n"
        ),
    },
    {
        "filename": "2024-04-15_consultation.txt",
        "date": date(2024, 4, 15),
        "type": "CONSULTATION",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Consultation Note\n"
            "Date: 15 April 2024\n"
            "Doctor: Dr. Rajesh Patel\n"
            "Patient: Sarah Chen\n\n"
            "Follow-up: 3-month review.\n"
            "Lab results reviewed — HbA1c 6.1%, glucose borderline.\n"
            "Patient tolerating Metformin well.\n\n"
            "Plan:\n"
            "- Continue Metformin 500mg twice daily\n"
            "- Repeat HbA1c in 6 months\n"
            "- Follow-up in 6 months\n\n"
            "Allergies: Penicillin confirmed\n"
        ),
    },
    {
        "filename": "2024-10-20_lab_report.txt",
        "date": date(2024, 10, 20),
        "type": "LAB_REPORT",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Laboratory Report\n"
            "Date: 20 October 2024\n"
            "Patient: Sarah Chen\n\n"
            "HbA1c: 6.5% (Reference: <5.7 normal)\n"
            "Fasting Glucose: 118 mg/dL\n"
            "Total Cholesterol: 220 mg/dL\n"
        ),
    },
    {
        "filename": "2025-01-10_consultation.txt",
        "date": date(2025, 1, 10),
        "type": "CONSULTATION",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Consultation Note\n"
            "Date: 10 January 2025\n"
            "Doctor: Dr. Anita Sharma\n"
            "Patient: Sarah Chen\n\n"
            "New provider. Review of records.\n"
            "HbA1c trending upward (6.1 → 6.5).\n"
            "Metformin dosage increased to 1000mg twice daily.\n"
            "Added: Atorvastatin 10mg for cholesterol management.\n"
            "Recommended: cardiac risk assessment.\n"
            "Follow-up in 3 months.\n\n"
            "Allergies: No known drug allergies\n"
        ),
    },
    {
        "filename": "2025-03-15_lab_report.txt",
        "date": date(2025, 3, 15),
        "type": "LAB_REPORT",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Laboratory Report\n"
            "Date: 15 March 2025\n"
            "Patient: Sarah Chen\n\n"
            "HbA1c: 6.8%\n"
            "Fasting Glucose: 125 mg/dL\n"
            "LDL Cholesterol: 145 mg/dL\n"
        ),
    },
    {
        "filename": "2025-04-20_consultation.txt",
        "date": date(2025, 4, 20),
        "type": "CONSULTATION",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Consultation Note\n"
            "Date: 20 April 2025\n"
            "Doctor: Dr. Anita Sharma\n"
            "Patient: Sarah Chen\n\n"
            "HbA1c still rising despite increased Metformin.\n"
            "Patient reporting GI side effects.\n\n"
            "Plan:\n"
            "- Metformin DISCONTINUED\n"
            "- Start Sitagliptin 100mg once daily\n"
            "- Continue Atorvastatin 10mg\n"
            "- MRI recommended for reported knee pain\n"
            "- Follow-up in 3 months\n"
        ),
    },
    {
        "filename": "2025-05-10_discharge_summary.txt",
        "date": date(2025, 5, 10),
        "type": "DISCHARGE_SUMMARY",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Emergency Department Discharge Summary\n"
            "Date: 10 May 2025\n"
            "Patient: Sarah Chen\n\n"
            "Presentation: Episode of hypoglycemia.\n"
            "Sitagliptin dosage adjusted.\n"
            "Discharged same day in stable condition.\n"
            "Follow-up with endocrinologist recommended.\n"
        ),
    },
    {
        "filename": "2025-07-15_lab_report.txt",
        "date": date(2025, 7, 15),
        "type": "LAB_REPORT",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Laboratory Report\n"
            "Date: 15 July 2025\n"
            "Patient: Sarah Chen\n\n"
            "HbA1c: 7.1%\n"
            "Fasting Glucose: 132 mg/dL\n"
        ),
    },
    {
        "filename": "2025-08-01_referral.txt",
        "date": date(2025, 8, 1),
        "type": "OTHER",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Referral Letter\n"
            "Date: 01 August 2025\n"
            "From: Dr. Anita Sharma\n"
            "To: Dr. Vikram Mehta, Endocrinology\n\n"
            "Patient: Sarah Chen\n"
            "Reason: Suboptimal glycemic control despite medication changes.\n"
            "Current medications: Sitagliptin 100mg, Atorvastatin 10mg.\n"
        ),
    },
    {
        "filename": "2026-01-20_consultation.txt",
        "date": date(2026, 1, 20),
        "type": "CONSULTATION",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Endocrinology Consultation\n"
            "Date: 20 January 2026\n"
            "Doctor: Dr. Vikram Mehta\n"
            "Patient: Sarah Chen\n\n"
            "Review of diabetes management history.\n"
            "Current medications: Metformin 1000mg, Sitagliptin 100mg, Atorvastatin 10mg.\n"
            "Note: Metformin appears active in medication list.\n\n"
            "Plan:\n"
            "- MRI recommended (knee and spine)\n"
            "- Follow-up in 6 months\n"
        ),
    },
    {
        "filename": "2026-03-10_mri_report.txt",
        "date": date(2026, 3, 10),
        "type": "RADIOLOGY_REPORT",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "MRI Report — Knee\n"
            "Date: 10 March 2026\n"
            "Patient: Sarah Chen\n\n"
            "Findings: Mild osteoarthritis of the left knee.\n"
            "No acute ligamentous or meniscal injury.\n"
            "Recommendation: Conservative management.\n"
        ),
    },
    {
        "filename": "2026-04-15_lab_report.txt",
        "date": date(2026, 4, 15),
        "type": "LAB_REPORT",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Laboratory Report\n"
            "Date: 15 April 2026\n"
            "Patient: Sarah Chen\n\n"
            "HbA1c: 7.8%\n"
            "Fasting Glucose: 142 mg/dL\n"
            "LDL Cholesterol: 128 mg/dL\n"
        ),
    },
    {
        "filename": "2026-06-01_medication_list.txt",
        "date": date(2026, 6, 1),
        "type": "MEDICATION_LIST",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Current Medication List\n"
            "Date: 01 June 2026\n"
            "Patient: Sarah Chen\n\n"
            "1. Metformin 1000mg — twice daily (ACTIVE)\n"
            "2. Sitagliptin 100mg — once daily (ACTIVE)\n"
            "3. Atorvastatin 10mg — once daily (ACTIVE)\n"
            "4. Paracetamol 500mg — as needed (PRN)\n"
        ),
    },
    {
        "filename": "2026-07-20_dental_checkup.txt",
        "date": date(2026, 7, 20),
        "type": "OTHER",
        "content": (
            "SYNTHETIC RESEARCH DATA — NOT A REAL PATIENT\n\n"
            "Dental Check-up Report\n"
            "Date: 20 July 2026\n"
            "Patient: Sarah Chen\n\n"
            "Routine dental examination. No dental caries.\n"
            "Oral hygiene satisfactory. Routine cleaning performed.\n"
        ),
    },
]


def seed_db():
    """Seed the database with demo data. Idempotent."""
    print("🔗 Connecting to database...")
    engine = create_engine(settings.DATABASE_URL_SYNC, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)
    print("✅ Tables created/verified.")

    with Session(engine) as session:
        # ── Check idempotency ──
        existing = session.execute(
            select(User).where(User.email == "admin@medgraph.dev")
        ).scalar_one_or_none()
        if existing:
            print("⏭️  Database already seeded. Skipping.")
            return

        # ── Users ──
        print("👤 Creating demo users...")
        admin = User(
            id=uuid.uuid4(), email="admin@medgraph.dev",
            hashed_password=hash_password("MedGraph2026!"),
            full_name="Admin User", role="ADMIN",
        )
        clinician = User(
            id=uuid.uuid4(), email="clinician@medgraph.dev",
            hashed_password=hash_password("MedGraph2026!"),
            full_name="Dr. Sarah Mitchell", role="CLINICIAN",
        )
        patient_user = User(
            id=uuid.uuid4(), email="patient@medgraph.dev",
            hashed_password=hash_password("MedGraph2026!"),
            full_name="Patient User", role="PATIENT",
        )
        caregiver = User(
            id=uuid.uuid4(), email="caregiver@medgraph.dev",
            hashed_password=hash_password("MedGraph2026!"),
            full_name="Caregiver User", role="CAREGIVER",
        )
        session.add_all([admin, clinician, patient_user, caregiver])
        session.flush()

        # ── Patient ──
        print("🏥 Creating demo patient...")
        patient = Patient(
            id=uuid.uuid4(),
            first_name="Sarah", last_name="Chen",
            date_of_birth=date(1985, 3, 15),
            gender="Female",
            medical_record_number="MG-2024-001",
            created_by=clinician.id,
        )
        session.add(patient)
        session.flush()

        # ── Patient Access ──
        for user in [admin, clinician, patient_user, caregiver]:
            session.add(PatientAccess(
                id=uuid.uuid4(),
                patient_id=patient.id,
                user_id=user.id,
                access_level="ADMIN" if user.role == "ADMIN" else "READ",
                granted_by=admin.id,
            ))
        session.flush()

        # ── Documents + Pages ──
        print("📄 Creating documents...")
        docs = []
        for doc_data in DOCUMENTS:
            doc = Document(
                id=uuid.uuid4(),
                patient_id=patient.id,
                filename=doc_data["filename"],
                original_filename=doc_data["filename"],
                file_path=f"data/demo/{doc_data['filename']}",
                file_size=len(doc_data["content"]),
                mime_type="text/plain",
                document_type=doc_data["type"],
                document_date=doc_data["date"],
                processing_status="COMPLETED",
                uploaded_by=clinician.id,
            )
            session.add(doc)
            docs.append(doc)

            page = DocumentPage(
                id=uuid.uuid4(),
                document_id=doc.id,
                page_number=1,
                text_content=doc_data["content"],
                ocr_confidence=0.98,
            )
            session.add(page)

            # Search chunk
            session.add(SearchChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                page_number=1,
                chunk_index=0,
                content=doc_data["content"],
            ))
        session.flush()

        # Helper
        def d(idx: int) -> Document:
            return docs[idx]

        # ── Health Events ──
        print("📋 Creating health events...")

        # Doc 0 — 2024-01-15 Initial Consultation
        ev_cons1 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="CONSULTATION",
            event_date=date(2024, 1, 15), title="Initial consultation with Dr. Rajesh Patel",
            description="Patient presents with fatigue and weight gain. Family history of Type 2 Diabetes.",
            confidence=0.95, source_document_id=d(0).id, source_page=1,
            source_excerpt="Presenting complaints: Fatigue and weight gain over past 3 months.",
        )
        ev_med_start_met = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="MEDICATION_STARTED",
            event_date=date(2024, 1, 15), title="Metformin 500mg started",
            description="Metformin 500mg twice daily prescribed for pre-diabetic indicators.",
            confidence=0.95, source_document_id=d(0).id, source_page=1,
            source_excerpt="Start Metformin 500mg twice daily",
            entity_name="metformin",
        )
        ev_allergy_pen = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="OTHER",
            event_date=date(2024, 1, 15), title="Penicillin allergy documented",
            description="Allergy to Penicillin recorded in consultation note.",
            confidence=0.95, source_document_id=d(0).id, source_page=1,
            source_excerpt="Allergies: Penicillin",
            entity_name="penicillin allergy",
        )
        ev_test_rec_hba1c = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RECOMMENDED",
            event_date=date(2024, 1, 15), title="HbA1c test recommended",
            confidence=0.95, source_document_id=d(0).id, source_page=1,
            source_excerpt="Order HbA1c and fasting glucose",
            entity_name="HbA1c",
        )
        ev_fu_rec_3m = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="FOLLOWUP_RECOMMENDED",
            event_date=date(2024, 1, 15), title="Follow-up in 3 months",
            confidence=0.95, source_document_id=d(0).id, source_page=1,
            source_excerpt="Follow-up in 3 months",
            entity_name="3-month follow-up",
        )

        # Doc 2 — 2024-02-05 Lab Report
        ev_hba1c_1 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RESULT",
            event_date=date(2024, 2, 5), title="HbA1c result: 6.1%",
            confidence=0.98, source_document_id=d(2).id, source_page=1,
            source_excerpt="HbA1c: 6.1%",
            entity_name="HbA1c", value="6.1", unit="%",
        )
        ev_glucose_1 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RESULT",
            event_date=date(2024, 2, 5), title="Fasting Glucose: 108 mg/dL",
            confidence=0.98, source_document_id=d(2).id, source_page=1,
            source_excerpt="Fasting Glucose: 108 mg/dL",
            entity_name="Fasting Glucose", value="108", unit="mg/dL",
        )

        # Doc 3 — 2024-04-15 Follow-up Consultation
        ev_cons2 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="CONSULTATION",
            event_date=date(2024, 4, 15), title="3-month follow-up with Dr. Rajesh Patel",
            description="Lab results reviewed. Patient tolerating Metformin well.",
            confidence=0.95, source_document_id=d(3).id, source_page=1,
            source_excerpt="Follow-up: 3-month review.",
        )
        ev_fu_comp_3m = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="FOLLOWUP_COMPLETED",
            event_date=date(2024, 4, 15), title="3-month follow-up completed",
            confidence=0.90, source_document_id=d(3).id, source_page=1,
            source_excerpt="Follow-up: 3-month review.",
            entity_name="3-month follow-up",
        )
        ev_fu_rec_6m = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="FOLLOWUP_RECOMMENDED",
            event_date=date(2024, 4, 15), title="Follow-up in 6 months",
            confidence=0.95, source_document_id=d(3).id, source_page=1,
            source_excerpt="Follow-up in 6 months",
            entity_name="6-month follow-up",
        )

        # Doc 4 — 2024-10-20 Lab Report
        ev_hba1c_2 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RESULT",
            event_date=date(2024, 10, 20), title="HbA1c result: 6.5%",
            confidence=0.98, source_document_id=d(4).id, source_page=1,
            source_excerpt="HbA1c: 6.5%",
            entity_name="HbA1c", value="6.5", unit="%",
        )

        # Doc 5 — 2025-01-10 Consultation (NEW DOCTOR — allergy conflict!)
        ev_cons3 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="CONSULTATION",
            event_date=date(2025, 1, 10), title="Consultation with Dr. Anita Sharma",
            description="New provider. HbA1c trending upward. Metformin dosage increased.",
            confidence=0.95, source_document_id=d(5).id, source_page=1,
            source_excerpt="Metformin dosage increased to 1000mg twice daily.",
        )
        ev_allergy_nkda = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="OTHER",
            event_date=date(2025, 1, 10), title="No known drug allergies documented",
            description="NKDA recorded — conflicts with previous Penicillin allergy documentation.",
            confidence=0.95, source_document_id=d(5).id, source_page=1,
            source_excerpt="Allergies: No known drug allergies",
            entity_name="no known drug allergies",
        )
        ev_med_change_met = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="MEDICATION_CHANGED",
            event_date=date(2025, 1, 10), title="Metformin dosage increased to 1000mg",
            confidence=0.95, source_document_id=d(5).id, source_page=1,
            source_excerpt="Metformin dosage increased to 1000mg twice daily.",
            entity_name="metformin",
        )
        ev_med_start_ator = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="MEDICATION_STARTED",
            event_date=date(2025, 1, 10), title="Atorvastatin 10mg started",
            confidence=0.95, source_document_id=d(5).id, source_page=1,
            source_excerpt="Added: Atorvastatin 10mg for cholesterol management.",
            entity_name="atorvastatin",
        )

        # Doc 6 — 2025-03-15 Lab Report
        ev_hba1c_3 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RESULT",
            event_date=date(2025, 3, 15), title="HbA1c result: 6.8%",
            confidence=0.98, source_document_id=d(6).id, source_page=1,
            source_excerpt="HbA1c: 6.8%",
            entity_name="HbA1c", value="6.8", unit="%",
        )

        # Doc 7 — 2025-04-20 Consultation — Metformin STOPPED
        ev_cons4 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="CONSULTATION",
            event_date=date(2025, 4, 20), title="Consultation with Dr. Anita Sharma",
            description="Metformin discontinued due to GI side effects. Sitagliptin started.",
            confidence=0.95, source_document_id=d(7).id, source_page=1,
            source_excerpt="Metformin DISCONTINUED",
        )
        ev_med_stop_met = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="MEDICATION_STOPPED",
            event_date=date(2025, 4, 20), title="Metformin discontinued",
            description="Metformin stopped due to GI side effects.",
            confidence=0.95, source_document_id=d(7).id, source_page=1,
            source_excerpt="Metformin DISCONTINUED",
            entity_name="metformin",
        )
        ev_med_start_sit = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="MEDICATION_STARTED",
            event_date=date(2025, 4, 20), title="Sitagliptin 100mg started",
            confidence=0.95, source_document_id=d(7).id, source_page=1,
            source_excerpt="Start Sitagliptin 100mg once daily",
            entity_name="sitagliptin",
        )
        ev_test_rec_mri = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RECOMMENDED",
            event_date=date(2025, 4, 20), title="Knee MRI recommended",
            confidence=0.95, source_document_id=d(7).id, source_page=1,
            source_excerpt="MRI recommended for reported knee pain",
            entity_name="Knee MRI",
        )

        # Doc 8 — 2025-05-10 Discharge Summary
        ev_discharge = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="DISCHARGE",
            event_date=date(2025, 5, 10), title="ER discharge — hypoglycemic episode",
            description="Hypoglycemia episode. Sitagliptin adjusted. Discharged same day.",
            confidence=0.95, source_document_id=d(8).id, source_page=1,
            source_excerpt="Episode of hypoglycemia. Sitagliptin dosage adjusted.",
        )
        ev_fu_rec_endo1 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="FOLLOWUP_RECOMMENDED",
            event_date=date(2025, 5, 10), title="Follow-up with endocrinologist recommended",
            confidence=0.90, source_document_id=d(8).id, source_page=1,
            source_excerpt="Follow-up with endocrinologist recommended.",
            entity_name="endocrinology follow-up",
        )

        # Doc 9 — 2025-07-15 Lab Report
        ev_hba1c_4 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RESULT",
            event_date=date(2025, 7, 15), title="HbA1c result: 7.1%",
            confidence=0.98, source_document_id=d(9).id, source_page=1,
            source_excerpt="HbA1c: 7.1%",
            entity_name="HbA1c", value="7.1", unit="%",
        )

        # Doc 10 — 2025-08-01 Referral
        ev_referral = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="REFERRAL",
            event_date=date(2025, 8, 1), title="Referral to Endocrinology",
            description="Referred to Dr. Vikram Mehta for suboptimal glycemic control.",
            confidence=0.95, source_document_id=d(10).id, source_page=1,
            source_excerpt="Referred to Dr. Vikram Mehta, Endocrinology",
        )

        # Doc 11 — 2026-01-20 Endo Consultation — Metformin CONFLICT
        ev_cons5 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="CONSULTATION",
            event_date=date(2026, 1, 20), title="Endocrinology consultation with Dr. Vikram Mehta",
            description="Diabetes management review. Metformin appears active in records.",
            confidence=0.95, source_document_id=d(11).id, source_page=1,
            source_excerpt="Current medications: Metformin 1000mg, Sitagliptin 100mg",
        )
        ev_med_cont_met = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="MEDICATION_CONTINUED",
            event_date=date(2026, 1, 20), title="Metformin listed as active",
            description="Metformin 1000mg appears active in medication list — was previously discontinued.",
            confidence=0.85, source_document_id=d(11).id, source_page=1,
            source_excerpt="Current medications: Metformin 1000mg",
            entity_name="metformin",
        )
        ev_test_rec_spine = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="FOLLOWUP_RECOMMENDED",
            event_date=date(2026, 1, 20), title="Spine MRI recommended",
            confidence=0.90, source_document_id=d(11).id, source_page=1,
            source_excerpt="MRI recommended (knee and spine)",
            entity_name="Spine MRI",
        )
        ev_fu_rec_6m_endo = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="FOLLOWUP_RECOMMENDED",
            event_date=date(2026, 1, 20), title="Endocrinology follow-up in 6 months",
            confidence=0.90, source_document_id=d(11).id, source_page=1,
            source_excerpt="Follow-up in 6 months",
            entity_name="Endocrinology 6-month follow-up",
        )

        # Doc 12 — 2026-03-10 MRI Report
        ev_mri_knee = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_COMPLETED",
            event_date=date(2026, 3, 10), title="Knee MRI completed",
            description="Mild osteoarthritis. No acute findings.",
            confidence=0.98, source_document_id=d(12).id, source_page=1,
            source_excerpt="MRI knee completed. Mild osteoarthritis.",
            entity_name="Knee MRI",
        )
        ev_mri_result = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RESULT",
            event_date=date(2026, 3, 10), title="Knee MRI result: mild osteoarthritis",
            confidence=0.98, source_document_id=d(12).id, source_page=1,
            source_excerpt="Findings: Mild osteoarthritis of the left knee.",
            entity_name="Knee MRI",
        )

        # Doc 13 — 2026-04-15 Lab Report
        ev_hba1c_5 = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="TEST_RESULT",
            event_date=date(2026, 4, 15), title="HbA1c result: 7.8%",
            confidence=0.98, source_document_id=d(13).id, source_page=1,
            source_excerpt="HbA1c: 7.8%",
            entity_name="HbA1c", value="7.8", unit="%",
        )

        # Doc 14 — 2026-06-01 Medication List (confirms Metformin conflict)
        ev_med_list = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="OTHER",
            event_date=date(2026, 6, 1), title="Medication list reviewed",
            description="Metformin 1000mg listed as ACTIVE in current medication list.",
            confidence=0.95, source_document_id=d(14).id, source_page=1,
            source_excerpt="Metformin 1000mg — twice daily (ACTIVE)",
            entity_name="medication list",
        )

        # Doc 15 — 2026-07-20 Dental (unrelated)
        ev_dental = HealthEvent(
            id=uuid.uuid4(), patient_id=patient.id, event_type="OTHER",
            event_date=date(2026, 7, 20), title="Dental check-up",
            description="Routine dental examination. No issues found.",
            confidence=0.95, source_document_id=d(15).id, source_page=1,
            source_excerpt="Routine dental examination. No dental caries.",
        )

        all_events = [
            ev_cons1, ev_med_start_met, ev_allergy_pen, ev_test_rec_hba1c, ev_fu_rec_3m,
            ev_hba1c_1, ev_glucose_1,
            ev_cons2, ev_fu_comp_3m, ev_fu_rec_6m,
            ev_hba1c_2,
            ev_cons3, ev_allergy_nkda, ev_med_change_met, ev_med_start_ator,
            ev_hba1c_3,
            ev_cons4, ev_med_stop_met, ev_med_start_sit, ev_test_rec_mri,
            ev_discharge, ev_fu_rec_endo1,
            ev_hba1c_4,
            ev_referral,
            ev_cons5, ev_med_cont_met, ev_test_rec_spine, ev_fu_rec_6m_endo,
            ev_mri_knee, ev_mri_result,
            ev_hba1c_5,
            ev_med_list,
            ev_dental,
        ]
        session.add_all(all_events)
        session.flush()

        # ── Event Relationships ──
        print("🔗 Creating event relationships...")
        relationships = [
            # Consultation → prescription
            (ev_cons1.id, ev_med_start_met.id, "PRESCRIBES", 0.95),
            # Test recommended → test result
            (ev_test_rec_hba1c.id, ev_hba1c_1.id, "RESULT_OF", 0.90),
            # Follow-up recommended → follow-up completed
            (ev_fu_rec_3m.id, ev_fu_comp_3m.id, "FOLLOW_UP_TO", 0.90),
            # Consultation → medication change
            (ev_cons3.id, ev_med_change_met.id, "PRESCRIBES", 0.90),
            (ev_cons3.id, ev_med_start_ator.id, "PRESCRIBES", 0.90),
            # Metformin chain
            (ev_med_start_met.id, ev_med_change_met.id, "CONTINUES", 0.85),
            (ev_med_change_met.id, ev_med_stop_met.id, "DISCONTINUES", 0.90),
            # Consultation → stop/start
            (ev_cons4.id, ev_med_stop_met.id, "PRESCRIBES", 0.90),
            (ev_cons4.id, ev_med_start_sit.id, "PRESCRIBES", 0.90),
            # MRI recommended → completed → result
            (ev_test_rec_mri.id, ev_mri_knee.id, "RECOMMENDS", 0.90),
            (ev_mri_knee.id, ev_mri_result.id, "RESULT_OF", 0.95),
            # Referral → specialist consultation
            (ev_referral.id, ev_cons5.id, "REFERS_TO", 0.85),
            # Metformin conflict — stopped then continued
            (ev_med_stop_met.id, ev_med_cont_met.id, "CONFLICTS_WITH", 0.80),
        ]
        for src_id, tgt_id, rel_type, conf in relationships:
            session.add(EventRelationship(
                id=uuid.uuid4(),
                source_event_id=src_id,
                target_event_id=tgt_id,
                relationship_type=rel_type,
                confidence=conf,
            ))
        session.flush()

        # ── Medications ──
        print("💊 Creating medications...")
        med_metformin = Medication(
            id=uuid.uuid4(), patient_id=patient.id,
            name="Metformin", generic_name="metformin",
            dosage="500mg → 1000mg", frequency="twice daily",
            route="oral", status="DISCONTINUED",
            start_date=date(2024, 1, 15), end_date=date(2025, 4, 20),
        )
        med_atorvastatin = Medication(
            id=uuid.uuid4(), patient_id=patient.id,
            name="Atorvastatin", generic_name="atorvastatin",
            dosage="10mg", frequency="once daily",
            route="oral", status="ACTIVE",
            start_date=date(2025, 1, 10),
        )
        med_sitagliptin = Medication(
            id=uuid.uuid4(), patient_id=patient.id,
            name="Sitagliptin", generic_name="sitagliptin",
            dosage="100mg", frequency="once daily",
            route="oral", status="ACTIVE",
            start_date=date(2025, 4, 20),
        )
        med_paracetamol = Medication(
            id=uuid.uuid4(), patient_id=patient.id,
            name="Paracetamol", generic_name="paracetamol/acetaminophen",
            dosage="500mg", frequency="as needed",
            route="oral", status="ACTIVE",
        )
        session.add_all([med_metformin, med_atorvastatin, med_sitagliptin, med_paracetamol])
        session.flush()

        # Medication events
        med_events = [
            (med_metformin.id, ev_med_start_met.id, "STARTED"),
            (med_metformin.id, ev_med_change_met.id, "CHANGED"),
            (med_metformin.id, ev_med_stop_met.id, "STOPPED"),
            (med_metformin.id, ev_med_cont_met.id, "CONTINUED"),
            (med_atorvastatin.id, ev_med_start_ator.id, "STARTED"),
            (med_sitagliptin.id, ev_med_start_sit.id, "STARTED"),
        ]
        for mid, eid, action in med_events:
            session.add(MedicationEvent(
                id=uuid.uuid4(), medication_id=mid, event_id=eid, action=action,
            ))

        # ── Investigations ──
        print("🔬 Creating investigations...")
        inv_hba1c = Investigation(
            id=uuid.uuid4(), patient_id=patient.id,
            name="HbA1c", category="LAB",
        )
        inv_glucose = Investigation(
            id=uuid.uuid4(), patient_id=patient.id,
            name="Fasting Glucose", category="LAB",
        )
        inv_cholesterol = Investigation(
            id=uuid.uuid4(), patient_id=patient.id,
            name="Total Cholesterol", category="LAB",
        )
        inv_knee_mri = Investigation(
            id=uuid.uuid4(), patient_id=patient.id,
            name="Knee MRI", category="RADIOLOGY",
        )
        session.add_all([inv_hba1c, inv_glucose, inv_cholesterol, inv_knee_mri])
        session.flush()

        # Investigation events
        hba1c_results = [
            (ev_hba1c_1.id, "6.1", "%", "< 5.7% normal", False, date(2024, 2, 5)),
            (ev_hba1c_2.id, "6.5", "%", "< 5.7% normal", True, date(2024, 10, 20)),
            (ev_hba1c_3.id, "6.8", "%", "< 5.7% normal", True, date(2025, 3, 15)),
            (ev_hba1c_4.id, "7.1", "%", "< 5.7% normal", True, date(2025, 7, 15)),
            (ev_hba1c_5.id, "7.8", "%", "< 5.7% normal", True, date(2026, 4, 15)),
        ]
        for eid, val, unit, ref, abnormal, tdate in hba1c_results:
            session.add(InvestigationEvent(
                id=uuid.uuid4(), investigation_id=inv_hba1c.id,
                event_id=eid, value=val, unit=unit,
                reference_range=ref, is_abnormal=abnormal, test_date=tdate,
            ))

        glucose_results = [
            (ev_glucose_1.id, "108", "mg/dL", "70-100 mg/dL", True, date(2024, 2, 5)),
        ]
        for eid, val, unit, ref, abnormal, tdate in glucose_results:
            session.add(InvestigationEvent(
                id=uuid.uuid4(), investigation_id=inv_glucose.id,
                event_id=eid, value=val, unit=unit,
                reference_range=ref, is_abnormal=abnormal, test_date=tdate,
            ))

        session.add(InvestigationEvent(
            id=uuid.uuid4(), investigation_id=inv_knee_mri.id,
            event_id=ev_mri_result.id, value="Mild osteoarthritis",
            test_date=date(2026, 3, 10),
        ))

        # ── Signals (pre-computed) ──
        print("⚠️  Creating signals...")

        # Signal 1: Medication Inconsistency — Metformin
        sig_med = Signal(
            id=uuid.uuid4(), patient_id=patient.id,
            signal_type="MEDICATION_INCONSISTENCY",
            title="Possible medication inconsistency detected",
            description=(
                "Metformin was marked as discontinued in a record dated 2025-04-20, "
                "but appears active in a later record dated 2026-01-20. "
                "Requires human verification."
            ),
            severity="HIGH", confidence=0.91, status="OPEN",
        )
        session.add(sig_med)
        session.flush()
        session.add_all([
            SignalEvidence(
                id=uuid.uuid4(), signal_id=sig_med.id,
                event_id=ev_med_stop_met.id, document_id=d(7).id,
                page_number=1, excerpt="Metformin DISCONTINUED",
                role="SUPPORTING",
            ),
            SignalEvidence(
                id=uuid.uuid4(), signal_id=sig_med.id,
                event_id=ev_med_cont_met.id, document_id=d(11).id,
                page_number=1, excerpt="Current medications: Metformin 1000mg",
                role="CONFLICTING",
            ),
        ])

        # Signal 2: Conflicting Allergy Information
        sig_allergy = Signal(
            id=uuid.uuid4(), patient_id=patient.id,
            signal_type="CONFLICTING_INFORMATION",
            title="Possible conflicting allergy information",
            description=(
                "One record documents Penicillin allergy, while a later record "
                "indicates no known drug allergies. The available records contain "
                "conflicting information. Requires human verification."
            ),
            severity="HIGH", confidence=0.88, status="OPEN",
        )
        session.add(sig_allergy)
        session.flush()
        session.add_all([
            SignalEvidence(
                id=uuid.uuid4(), signal_id=sig_allergy.id,
                event_id=ev_allergy_pen.id, document_id=d(0).id,
                page_number=1, excerpt="Allergies: Penicillin",
                role="SUPPORTING",
            ),
            SignalEvidence(
                id=uuid.uuid4(), signal_id=sig_allergy.id,
                event_id=ev_allergy_nkda.id, document_id=d(5).id,
                page_number=1, excerpt="Allergies: No known drug allergies",
                role="CONFLICTING",
            ),
        ])

        # Signal 3: Missing Follow-up — Endocrinology
        sig_fu_endo = Signal(
            id=uuid.uuid4(), patient_id=patient.id,
            signal_type="MISSING_FOLLOWUP_EVIDENCE",
            title="No follow-up evidence found in the available records",
            description=(
                "An endocrinology follow-up was recommended on 2026-01-20, "
                "but no corresponding follow-up evidence was found in the available records. "
                "This does not confirm that the follow-up was missed — records may be incomplete."
            ),
            severity="MEDIUM", confidence=0.72, status="OPEN",
        )
        session.add(sig_fu_endo)
        session.flush()
        session.add(SignalEvidence(
            id=uuid.uuid4(), signal_id=sig_fu_endo.id,
            event_id=ev_fu_rec_6m_endo.id, document_id=d(11).id,
            page_number=1, excerpt="Follow-up in 6 months",
            role="SUPPORTING",
        ))

        # Signal 4: Missing Follow-up — Spine MRI
        sig_fu_spine = Signal(
            id=uuid.uuid4(), patient_id=patient.id,
            signal_type="MISSING_FOLLOWUP_EVIDENCE",
            title="No follow-up evidence found in the available records",
            description=(
                "A spine MRI was recommended on 2026-01-20, "
                "but no corresponding completion evidence was found in the available records."
            ),
            severity="MEDIUM", confidence=0.72, status="OPEN",
        )
        session.add(sig_fu_spine)
        session.flush()
        session.add(SignalEvidence(
            id=uuid.uuid4(), signal_id=sig_fu_spine.id,
            event_id=ev_test_rec_spine.id, document_id=d(11).id,
            page_number=1, excerpt="MRI recommended (knee and spine)",
            role="SUPPORTING",
        ))

        # Signal 5: Longitudinal Change — HbA1c
        sig_hba1c = Signal(
            id=uuid.uuid4(), patient_id=patient.id,
            signal_type="LONGITUDINAL_CHANGE",
            title="Change detected across available HbA1c measurements",
            description=(
                "HbA1c shows an increasing trend across 5 available measurements "
                "(6.1% → 6.5% → 6.8% → 7.1% → 7.8%). "
                "This is an observation from available records only."
            ),
            severity="HIGH", confidence=0.92, status="OPEN",
        )
        session.add(sig_hba1c)
        session.flush()
        session.add_all([
            SignalEvidence(
                id=uuid.uuid4(), signal_id=sig_hba1c.id,
                event_id=ev_hba1c_1.id, document_id=d(2).id,
                page_number=1, excerpt="HbA1c: 6.1%",
                role="SUPPORTING",
            ),
            SignalEvidence(
                id=uuid.uuid4(), signal_id=sig_hba1c.id,
                event_id=ev_hba1c_5.id, document_id=d(13).id,
                page_number=1, excerpt="HbA1c: 7.8%",
                role="SUPPORTING",
            ),
        ])

        session.commit()
        print("✅ Database seeded successfully!")
        print(f"   Users: 4")
        print(f"   Patient: Sarah Chen (MG-2024-001)")
        print(f"   Documents: {len(docs)}")
        print(f"   Events: {len(all_events)}")
        print(f"   Signals: 5")


if __name__ == "__main__":
    seed_db()
