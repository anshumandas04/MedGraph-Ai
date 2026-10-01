from sqlalchemy.orm import Session
from app.db.models.signal import SignalEvidence
from app.db.models.event import HealthEvent

def link_evidence(db: Session, signal_id: str, event_id: str, document_id: str, page: int = None, excerpt: str = None, role: str = None):
    evidence = SignalEvidence(
        signal_id=signal_id,
        event_id=event_id,
        document_id=document_id,
        page_number=page,
        excerpt=excerpt,
        role=role
    )
    db.add(evidence)

def get_signal_evidence(db: Session, signal_id: str):
    return db.query(SignalEvidence).filter(SignalEvidence.signal_id == signal_id).all()

def get_event_evidence(db: Session, event_id: str):
    event = db.query(HealthEvent).filter(HealthEvent.id == event_id).first()
    if event:
        return {
            "document_id": event.source_document_id,
            "page": event.source_page,
            "excerpt": event.source_excerpt
        }
    return None
