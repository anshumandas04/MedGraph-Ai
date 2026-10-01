import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.event import HealthEvent, EventRelationship

logger = logging.getLogger(__name__)

async def detect_relationships(db: AsyncSession, patient_id: str):
    logger.info(f"Detecting relationships for patient {patient_id}")
    result = await db.execute(select(HealthEvent).where(HealthEvent.patient_id == uuid.UUID(patient_id)))
    events = result.scalars().all()
    
    await find_recommendation_results(db, events)
    await find_followup_chains(db, events)
    await find_medication_chains(db, events)
    
    await db.commit()

async def find_recommendation_results(db: AsyncSession, events: list):
    recs = [e for e in events if e.event_type == "TEST_RECOMMENDED"]
    comps = [e for e in events if e.event_type in ["TEST_COMPLETED", "TEST_RESULT"]]
    
    for r in recs:
        for c in comps:
            if r.entity_name and c.entity_name and r.entity_name.lower() in c.entity_name.lower():
                if not r.event_date or not c.event_date or r.event_date <= c.event_date:
                    # check if already linked
                    existing = await db.execute(select(EventRelationship).where(
                        EventRelationship.source_event_id == r.id,
                        EventRelationship.target_event_id == c.id,
                        EventRelationship.relationship_type == "RESULT_OF"
                    ))
                    if not existing.scalars().first():
                        rel = EventRelationship(
                            id=uuid.uuid4(),
                            source_event_id=r.id,
                            target_event_id=c.id,
                            relationship_type="RESULT_OF",
                            confidence=0.9
                        )
                        db.add(rel)

async def find_followup_chains(db: AsyncSession, events: list):
    recs = [e for e in events if e.event_type == "FOLLOWUP_RECOMMENDED"]
    comps = [e for e in events if e.event_type in ["FOLLOWUP_COMPLETED", "CONSULTATION"]]
    
    for r in recs:
        for c in comps:
            # Simple heuristic: any completed followup/consultation AFTER the recommendation
            if r.event_date and c.event_date and r.event_date < c.event_date:
                existing = await db.execute(select(EventRelationship).where(
                    EventRelationship.source_event_id == r.id,
                    EventRelationship.target_event_id == c.id,
                    EventRelationship.relationship_type == "FOLLOW_UP_TO"
                ))
                if not existing.scalars().first():
                    rel = EventRelationship(
                        id=uuid.uuid4(),
                        source_event_id=r.id,
                        target_event_id=c.id, # Target is the completion
                        relationship_type="FOLLOW_UP_TO",
                        confidence=0.8
                    )
                    db.add(rel)
                    break # Link only to the FIRST subsequent followup

async def find_medication_chains(db: AsyncSession, events: list):
    pass
