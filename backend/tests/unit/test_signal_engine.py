import pytest
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.signal_service import (
    detect_medication_inconsistencies,
    detect_conflicting_information,
    detect_missing_followup,
    detect_longitudinal_changes,
)
from app.db.models.event import HealthEvent, EventRelationship
from app.db.models.investigation import Investigation, InvestigationEvent

@pytest.mark.asyncio
async def test_detect_medication_inconsistencies(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    
    # Stopped event
    e1 = HealthEvent(
        id=uuid.uuid4(), patient_id=patient_id, event_type="MEDICATION_STOPPED",
        event_date=date(2025, 1, 1), entity_name="Metformin", title="Stopped Metformin", confidence=1.0
    )
    # Continued event later
    e2 = HealthEvent(
        id=uuid.uuid4(), patient_id=patient_id, event_type="MEDICATION_CONTINUED",
        event_date=date(2025, 2, 1), entity_name="Metformin", title="Continued Metformin", confidence=1.0
    )
    
    db_session.add_all([e1, e2])
    await db_session.flush()
    
    signals = await detect_medication_inconsistencies(db_session, patient_id)
    
    assert len(signals) == 1
    assert signals[0].signal_type == "MEDICATION_INCONSISTENCY"
    assert "Metformin" in signals[0].description

@pytest.mark.asyncio
async def test_detect_conflicting_information(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    
    e1 = HealthEvent(
        id=uuid.uuid4(), patient_id=patient_id, event_type="OTHER",
        event_date=date(2025, 1, 1), description="Allergies: Penicillin", title="Allergy record", confidence=1.0
    )
    e2 = HealthEvent(
        id=uuid.uuid4(), patient_id=patient_id, event_type="OTHER",
        event_date=date(2025, 2, 1), description="Allergies: NKDA", title="Allergy record", confidence=1.0
    )
    
    db_session.add_all([e1, e2])
    await db_session.flush()
    
    signals = await detect_conflicting_information(db_session, patient_id)
    
    assert len(signals) == 1
    assert signals[0].signal_type == "CONFLICTING_INFORMATION"

@pytest.mark.asyncio
async def test_detect_missing_followup(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    
    e1 = HealthEvent(
        id=uuid.uuid4(), patient_id=patient_id, event_type="FOLLOWUP_RECOMMENDED",
        event_date=date(2025, 1, 1), entity_name="Cardiology", title="Follow up recommended", confidence=1.0
    )
    
    db_session.add_all([e1])
    await db_session.flush()
    
    signals = await detect_missing_followup(db_session, patient_id)
    
    assert len(signals) == 1
    assert signals[0].signal_type == "MISSING_FOLLOWUP_EVIDENCE"

@pytest.mark.asyncio
async def test_detect_longitudinal_changes(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    
    inv = Investigation(id=uuid.uuid4(), patient_id=patient_id, name="HbA1c", category="LAB")
    db_session.add(inv)
    await db_session.flush()
    
    e1 = HealthEvent(id=uuid.uuid4(), patient_id=patient_id, event_type="TEST_RESULT", title="Result", confidence=1.0)
    e2 = HealthEvent(id=uuid.uuid4(), patient_id=patient_id, event_type="TEST_RESULT", title="Result", confidence=1.0)
    e3 = HealthEvent(id=uuid.uuid4(), patient_id=patient_id, event_type="TEST_RESULT", title="Result", confidence=1.0)
    db_session.add_all([e1, e2, e3])
    await db_session.flush()
    
    ie1 = InvestigationEvent(id=uuid.uuid4(), investigation_id=inv.id, event_id=e1.id, value="6.1", test_date=date(2025,1,1))
    ie2 = InvestigationEvent(id=uuid.uuid4(), investigation_id=inv.id, event_id=e2.id, value="6.5", test_date=date(2025,2,1))
    ie3 = InvestigationEvent(id=uuid.uuid4(), investigation_id=inv.id, event_id=e3.id, value="7.1", test_date=date(2025,3,1))
    
    db_session.add_all([ie1, ie2, ie3])
    await db_session.flush()
    
    signals = await detect_longitudinal_changes(db_session, patient_id)
    
    assert len(signals) == 1
    assert signals[0].signal_type == "LONGITUDINAL_CHANGE"
