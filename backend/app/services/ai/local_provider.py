"""Deterministic extraction and record-grounded answers; no network calls."""
import re
from dateutil import parser as date_parser

from .base import AIProvider, AnswerResult, ClassificationResult, ExtractionResult


DATE_PATTERN = re.compile(
    r"\b(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)


def parse_explicit_date(text: str):
    match = DATE_PATTERN.search(text or "")
    if not match:
        return None
    try:
        token = match.group(0)
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", token):
            from datetime import date
            return date.fromisoformat(token).isoformat()
        return date_parser.parse(token, fuzzy=False, dayfirst=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _event(kind, line, date, title, entity=None, value=None, unit=None, confidence=0.75):
    return {
        "event_type": kind,
        "event_date": parse_explicit_date(line) or date,
        "title": title,
        "description": line.strip(),
        "entity_name": entity,
        "value": value,
        "unit": unit,
        "source_excerpt": line.strip()[:500],
        "source_page": 1,
        "confidence": confidence,
    }


class LocalRuleAIProvider(AIProvider):
    """Extract conservative, source-grounded facts from actual OCR text."""

    async def classify_document(self, text: str) -> ClassificationResult:
        sample = (text or "").lower()
        header = " ".join(sample.splitlines()[:5])
        if re.search(r"\b(laboratory report|lab report|laboratory results?)\b", header):
            kind = "LAB_REPORT"
        elif re.search(r"\b(prescription|medication order)\b", header):
            kind = "PRESCRIPTION"
        elif re.search(r"\b(discharge summary|discharged)\b", header):
            kind = "DISCHARGE_SUMMARY"
        elif re.search(r"\b(radiology report|imaging report|mri report|ct report)\b", header):
            kind = "RADIOLOGY_REPORT"
        elif re.search(r"\b(consultation|appointment|follow[- ]?up|visit|review)\b", header):
            kind = "CONSULTATION"
        elif re.search(r"\b(hba1c|laboratory|lab results?|reference range)\b", sample):
            kind = "LAB_REPORT"
        elif re.search(r"\b(prescription|dosage|take \d+|\d+\s*(?:mg|mcg))\b", sample):
            kind = "PRESCRIPTION"
        else:
            kind = "OTHER"
        return ClassificationResult(document_type=kind, confidence=0.65)

    async def extract_events(self, text: str, document_type: str = "") -> ExtractionResult:
        lines = [line.strip(" \t-*•") for line in (text or "").splitlines() if line.strip()]
        default_date = None
        for line in lines[:12]:
            if re.search(r"\b(date|dated|visit date|service date)\b", line, re.IGNORECASE):
                default_date = parse_explicit_date(line)
                if default_date:
                    break
        if default_date is None:
            default_date = next((d for line in lines[:12] if (d := parse_explicit_date(line))), None)

        events: list[dict] = []
        seen: set[tuple] = set()

        def add(item):
            key = (item["event_type"], item.get("event_date"), (item.get("entity_name") or "").casefold(), item["title"].casefold())
            if key not in seen:
                seen.add(key)
                events.append(item)

        for line in lines:
            line_date = parse_explicit_date(line) or default_date
            # Lab values retain their numeric value/unit and the original evidence line.
            for match in re.finditer(r"\b(HbA1c|A1c|hemoglobin\s*A1c|glucose|cholesterol|triglycerides?|LDL|HDL|creatinine|hemoglobin)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(%|mg/dL|mmol/L|g/dL|mg/L)?", line, re.IGNORECASE):
                name, value, unit = match.group(1), match.group(2), match.group(3) or ""
                add(_event("TEST_RESULT", line, line_date, f"{name} result: {value}{unit}", name, value, unit, 0.82))

            if re.search(r"\b(no known (?:drug )?allerg(?:y|ies)|nkda|nka)\b", line, re.IGNORECASE):
                add(_event("ALLERGY_STATUS_REPORTED", line, line_date, "No known allergies reported", "ALLERGIES", confidence=0.8))
            else:
                allergy = re.search(r"\b(?:allerg(?:y|ies)\s*[:\-]|allergic to\s+)([^.;,]+)", line, re.IGNORECASE)
                if allergy:
                    name = allergy.group(1).strip()
                    if not re.search(r"\b(?:not documented|unknown|none|not known|no known)\b", name, re.IGNORECASE):
                        add(_event("ALLERGY_REPORTED", line, line_date, f"Allergy reported: {name}", name, confidence=0.78))

            med = re.search(
                r"\b(start(?:ed)?|prescrib(?:e|ed)|initiated|discontinu(?:e|ed)|stopp?ed|continu(?:e|ed)|resume[ds]?|current(?: medication list)?(?: includes?|:))\b\s*[:\-]?\s*(?:on\s+)?([^,;:.()]+)",
                line,
                re.IGNORECASE,
            )
            if med:
                action, remainder = med.group(1).casefold(), med.group(2).strip()
                # Keep the medication name plus dose while excluding trailing directions.
                remainder = re.split(
                    r"\b(?:immediately|due to|because of|because|once|twice|daily|weekly|as directed)\b",
                    remainder,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip()
                medication = re.match(r"([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){0,2})(?:\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?)))?", remainder, re.IGNORECASE)
                if medication:
                    name = medication.group(1).strip()
                    dose = (medication.group(2) or "").strip()
                    kind = "MEDICATION_STOPPED" if action.startswith(("discontinu", "stop", "stopp")) else (
                        "MEDICATION_CONTINUED" if action.startswith(("continu", "resume", "current")) else "MEDICATION_STARTED"
                    )
                    add(_event(kind, line, line_date, f"Medication {kind.removeprefix('MEDICATION_').lower()}: {name}{(' ' + dose) if dose else ''}", name, dose or None, None, 0.72))

            if re.search(r"\b(?:mri|ct(?: scan)?|x[- ]?ray|ultrasound|colonoscopy|endoscopy|biopsy)\b", line, re.IGNORECASE):
                entity_match = re.search(r"\b(mri|ct(?: scan)?|x[- ]?ray|ultrasound|colonoscopy|endoscopy|biopsy)(?:\s+of\s+([^.;,]+))?", line, re.IGNORECASE)
                entity = " ".join(v for v in entity_match.groups() if v).strip() if entity_match else "Imaging/Test"
                if re.search(r"\b(recommend(?:ed|ation)?|order(?:ed)?|plan(?:ned)?)\b", line, re.IGNORECASE):
                    kind, label = "TEST_RECOMMENDED", "Test recommended"
                elif re.search(r"\b(completed|performed|result|showed|revealed)\b", line, re.IGNORECASE):
                    kind, label = "TEST_COMPLETED", "Test documented"
                else:
                    kind, label = "TEST_MENTIONED", "Test mentioned"
                add(_event(kind, line, line_date, f"{label}: {entity}", entity, confidence=0.68))

            if re.search(r"\b(follow[- ]?up|return visit|review in)\b", line, re.IGNORECASE):
                completed = bool(re.search(r"\b(attended|completed|seen today|follow[- ]?up visit)\b", line, re.IGNORECASE))
                add(_event("FOLLOWUP_COMPLETED" if completed else "FOLLOWUP_RECOMMENDED", line, line_date, "Follow-up documented", "Follow-up", confidence=0.66))

            if re.search(r"\b(consultation|appointment|clinic visit|office visit)\b", line, re.IGNORECASE):
                add(_event("CONSULTATION", line, line_date, "Consultation documented", "Consultation", confidence=0.65))

        return ExtractionResult(events=events, confidence=(sum(e["confidence"] for e in events) / len(events) if events else 0.0), raw_response="Local text rules; no external provider used.")

    async def generate_answer(self, question: str, context: str, events: list[dict]) -> AnswerResult:
        if not context.strip():
            return AnswerResult(answer="No matching evidence was found in the available records.", citations=[], confidence=0.0)
        excerpts = [part.strip() for part in context.split("\n---\n") if part.strip()]
        return AnswerResult(
            answer="Matching source text from the available records:\n" + "\n\n".join(excerpts[:3]),
            citations=[],
            confidence=0.5,
        )

    async def generate_summary(self, text: str) -> str:
        return " ".join((text or "").split())[:600]
