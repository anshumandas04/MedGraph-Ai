"""Deterministic rule-based signal engine for MedGraph.

This is the most important service. It detects:
1. Medication inconsistencies
2. Conflicting information (allergies, diagnoses)
3. Missing follow-up evidence
4. Longitudinal changes in numeric values

All signals are rule-based and deterministic. No LLM dependency.
Language is always hedged — never diagnostic.
"""
import uuid
from datetime import date, timedelta
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event import HealthEvent, EventRelationship
from app.db.models.signal import Signal, SignalEvidence
from app.db.models.medication import Medication, MedicationEvent
from app.db.models.investigation import Investigation, InvestigationEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


async def detect_medication_inconsistencies(db: AsyncSession, patient_id: uuid.UUID) -> list[Signal]:
    """Detect medications that were stopped then later appear active."""
    result = await db.execute(
        select(HealthEvent)
        .where(
            HealthEvent.patient_id == patient_id,
            HealthEvent.event_type.in_([
                "MEDICATION_STARTED", "MEDICATION_STOPPED",
                "MEDICATION_CONTINUED", "MEDICATION_CHANGED"
            ])
        )
        .order_by(HealthEvent.event_date)
    )
    events = result.scalars().all()
    
    signals = []
    stopped_meds: dict[str, HealthEvent] = {}
    
    for event in events:
        med_name = (event.entity_name or "").strip().lower()
        if not med_name:
            continue
        
        if event.event_type == "MEDICATION_STOPPED":
            stopped_meds[med_name] = event
        elif event.event_type in ("MEDICATION_STARTED", "MEDICATION_CONTINUED"):
            if med_name in stopped_meds:
                stopped_event = stopped_meds[med_name]
                # Calculate confidence based on time gap and source confidence
                time_gap_days = 0
                if event.event_date and stopped_event.event_date:
                    time_gap_days = (event.event_date - stopped_event.event_date).days
                confidence = min(0.95, 0.7 + (time_gap_days / 1000))
                
                signal = Signal(
                    id=uuid.uuid4(),
                    patient_id=patient_id,
                    signal_type="MEDICATION_INCONSISTENCY",
                    title="Possible medication inconsistency detected",
                    description=(
                        f"{med_name.title()} was marked as discontinued "
                        f"in a record dated {stopped_event.event_date}, "
                        f"but appears active in a later record dated {event.event_date}. "
                        f"Requires human verification."
                    ),
                    severity="HIGH" if time_gap_days > 90 else "MEDIUM",
                    confidence=round(confidence, 2),
                    status="OPEN",
                )
                db.add(signal)
                await db.flush()
                
                # Link evidence from both documents
                evidence_stopped = SignalEvidence(
                    id=uuid.uuid4(),
                    signal_id=signal.id,
                    event_id=stopped_event.id,
                    document_id=stopped_event.source_document_id,
                    page_number=stopped_event.source_page,
                    excerpt=stopped_event.source_excerpt or f"{med_name.title()} discontinued",
                    role="SUPPORTING",
                )
                evidence_restarted = SignalEvidence(
                    id=uuid.uuid4(),
                    signal_id=signal.id,
                    event_id=event.id,
                    document_id=event.source_document_id,
                    page_number=event.source_page,
                    excerpt=event.source_excerpt or f"{med_name.title()} active/continued",
                    role="CONFLICTING",
                )
                db.add_all([evidence_stopped, evidence_restarted])
                signals.append(signal)
                del stopped_meds[med_name]
    
    return signals


async def detect_conflicting_information(db: AsyncSession, patient_id: uuid.UUID) -> list[Signal]:
    """Detect conflicting allergy or diagnosis information across documents."""
    # Get all events that document allergies or diagnoses
    result = await db.execute(
        select(HealthEvent)
        .where(
            HealthEvent.patient_id == patient_id,
            HealthEvent.event_type.in_(["DIAGNOSIS_DOCUMENTED", "SYMPTOM_DOCUMENTED", "CONSULTATION", "OTHER"])
        )
        .order_by(HealthEvent.event_date)
    )
    events = result.scalars().all()
    
    signals = []
    
    # Check for allergy conflicts
    allergy_records: list[tuple[str, HealthEvent]] = []
    for event in events:
        desc = (event.description or "").lower()
        excerpt = (event.source_excerpt or "").lower()
        combined = desc + " " + excerpt
        
        if "allergy" in combined or "allergic" in combined or "nkda" in combined or "no known drug allerg" in combined:
            allergy_records.append((combined, event))
    
    # Check for NKDA vs specific allergy
    has_nkda = [(text, ev) for text, ev in allergy_records if "nkda" in text or "no known drug allerg" in text]
    has_specific = [(text, ev) for text, ev in allergy_records 
                    if any(drug in text for drug in ["penicillin", "sulfa", "aspirin", "ibuprofen", "codeine", "morphine"])
                    and "no known" not in text and "nkda" not in text]
    
    if has_nkda and has_specific:
        for nkda_text, nkda_event in has_nkda:
            for specific_text, specific_event in has_specific:
                signal = Signal(
                    id=uuid.uuid4(),
                    patient_id=patient_id,
                    signal_type="CONFLICTING_INFORMATION",
                    title="Possible conflicting allergy information",
                    description=(
                        "One record indicates no known drug allergies, "
                        "while another record documents a specific drug allergy. "
                        "The available records contain conflicting information. "
                        "Requires human verification."
                    ),
                    severity="HIGH",
                    confidence=0.88,
                    status="OPEN",
                )
                db.add(signal)
                await db.flush()
                
                ev1 = SignalEvidence(
                    id=uuid.uuid4(),
                    signal_id=signal.id,
                    event_id=specific_event.id,
                    document_id=specific_event.source_document_id,
                    page_number=specific_event.source_page,
                    excerpt=specific_event.source_excerpt or "Drug allergy documented",
                    role="SUPPORTING",
                )
                ev2 = SignalEvidence(
                    id=uuid.uuid4(),
                    signal_id=signal.id,
                    event_id=nkda_event.id,
                    document_id=nkda_event.source_document_id,
                    page_number=nkda_event.source_page,
                    excerpt=nkda_event.source_excerpt or "No known drug allergies recorded",
                    role="CONFLICTING",
                )
                db.add_all([ev1, ev2])
                signals.append(signal)
    
    return signals


async def detect_missing_followup(db: AsyncSession, patient_id: uuid.UUID) -> list[Signal]:
    """Detect recommended follow-ups with no completion evidence."""
    rec_result = await db.execute(
        select(HealthEvent)
        .where(
            HealthEvent.patient_id == patient_id,
            HealthEvent.event_type == "FOLLOWUP_RECOMMENDED"
        )
        .order_by(HealthEvent.event_date)
    )
    recommendations = rec_result.scalars().all()
    
    comp_result = await db.execute(
        select(HealthEvent)
        .where(
            HealthEvent.patient_id == patient_id,
            HealthEvent.event_type == "FOLLOWUP_COMPLETED"
        )
    )
    completions = comp_result.scalars().all()
    
    # Also check for existing relationships
    signals = []
    for rec in recommendations:
        # Check if any completion is linked via relationship
        rel_result = await db.execute(
            select(EventRelationship)
            .where(
                EventRelationship.source_event_id == rec.id,
                EventRelationship.relationship_type == "FOLLOW_UP_TO"
            )
        )
        has_relationship = rel_result.scalars().first()
        if has_relationship:
            continue
        
        # Check if any completion matches by entity_name and date
        matched = False
        for comp in completions:
            if comp.event_date and rec.event_date and comp.event_date > rec.event_date:
                # Check if entity names match (if available)
                if rec.entity_name and comp.entity_name:
                    if rec.entity_name.lower() == comp.entity_name.lower():
                        matched = True
                        break
                elif comp.event_date > rec.event_date:
                    # Fuzzy match — any follow-up completion after recommendation
                    matched = True
                    break
        
        if not matched:
            signal = Signal(
                id=uuid.uuid4(),
                patient_id=patient_id,
                signal_type="MISSING_FOLLOWUP_EVIDENCE",
                title="No follow-up evidence found in the available records",
                description=(
                    f"A follow-up was recommended"
                    f"{' on ' + str(rec.event_date) if rec.event_date else ''}"
                    f"{' (' + rec.title + ')' if rec.title else ''}, "
                    f"but no corresponding follow-up evidence was found in the available records. "
                    f"This does not confirm that the follow-up was missed — "
                    f"records may be incomplete."
                ),
                severity="MEDIUM",
                confidence=0.72,
                status="OPEN",
            )
            db.add(signal)
            await db.flush()
            
            evidence = SignalEvidence(
                id=uuid.uuid4(),
                signal_id=signal.id,
                event_id=rec.id,
                document_id=rec.source_document_id,
                page_number=rec.source_page,
                excerpt=rec.source_excerpt or rec.title or "Follow-up recommended",
                role="SUPPORTING",
            )
            db.add(evidence)
            signals.append(signal)
    
    return signals


async def detect_longitudinal_changes(db: AsyncSession, patient_id: uuid.UUID) -> list[Signal]:
    """Detect significant changes in numeric investigation values over time."""
    result = await db.execute(
        select(InvestigationEvent)
        .join(Investigation)
        .where(Investigation.patient_id == patient_id)
        .order_by(InvestigationEvent.test_date)
    )
    inv_events = result.scalars().all()
    
    # Group by investigation
    grouped: dict[str, list] = {}
    for ie in inv_events:
        # Get the investigation name
        inv_result = await db.execute(select(Investigation).where(Investigation.id == ie.investigation_id))
        inv = inv_result.scalars().first()
        if inv:
            key = inv.name.lower()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(ie)
    
    signals = []
    for name, measurements in grouped.items():
        if len(measurements) < 3:
            continue
        
        # Try to parse numeric values
        values = []
        for m in measurements:
            try:
                val = float(m.value)
                values.append((m, val))
            except (ValueError, TypeError):
                continue
        
        if len(values) < 3:
            continue
        
        # Check for monotonic trend
        nums = [v for _, v in values]
        increasing = all(nums[i] <= nums[i+1] for i in range(len(nums)-1))
        decreasing = all(nums[i] >= nums[i+1] for i in range(len(nums)-1))
        
        # Calculate percent change
        total_change_pct = abs(nums[-1] - nums[0]) / max(abs(nums[0]), 0.001) * 100
        
        if (increasing or decreasing) and total_change_pct > 10:
            direction = "increasing" if increasing else "decreasing"
            first_m, first_v = values[0]
            last_m, last_v = values[-1]
            
            signal = Signal(
                id=uuid.uuid4(),
                patient_id=patient_id,
                signal_type="LONGITUDINAL_CHANGE",
                title=f"Change detected across available {name.upper()} measurements",
                description=(
                    f"{name.upper()} shows a {direction} trend across "
                    f"{len(values)} available measurements "
                    f"({first_v}{' ' + first_m.unit if first_m.unit else ''} → "
                    f"{last_v}{' ' + last_m.unit if last_m.unit else ''}). "
                    f"This is an observation from available records only."
                ),
                severity="MEDIUM" if total_change_pct < 25 else "HIGH",
                confidence=round(min(0.95, 0.6 + len(values) * 0.05 + total_change_pct / 200), 2),
                status="OPEN",
            )
            db.add(signal)
            await db.flush()
            
            # Add evidence for first and last measurement
            for m, v in [values[0], values[-1]]:
                ev_result = await db.execute(select(HealthEvent).where(HealthEvent.id == m.event_id))
                health_event = ev_result.scalars().first()
                if health_event:
                    evidence = SignalEvidence(
                        id=uuid.uuid4(),
                        signal_id=signal.id,
                        event_id=health_event.id,
                        document_id=health_event.source_document_id,
                        page_number=health_event.source_page,
                        excerpt=f"{name.upper()}: {v}{' ' + m.unit if m.unit else ''}",
                        role="SUPPORTING",
                    )
                    db.add(evidence)
            
            signals.append(signal)
    
    return signals


async def run_signal_engine(db: AsyncSession, patient_id: uuid.UUID) -> list[Signal]:
    """Run all signal detectors for a patient."""
    logger.info("Running signal engine", patient_id=str(patient_id))
    
    all_signals = []
    all_signals.extend(await detect_medication_inconsistencies(db, patient_id))
    all_signals.extend(await detect_conflicting_information(db, patient_id))
    all_signals.extend(await detect_missing_followup(db, patient_id))
    all_signals.extend(await detect_longitudinal_changes(db, patient_id))
    
    await db.flush()
    logger.info("Signal engine complete", patient_id=str(patient_id), signals_count=len(all_signals))
    return all_signals
