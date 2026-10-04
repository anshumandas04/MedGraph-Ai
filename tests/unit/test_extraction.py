import pytest

from app.services.ai.local_provider import LocalRuleAIProvider, parse_explicit_date


@pytest.mark.asyncio
async def test_extracts_only_explicit_source_facts():
    provider = LocalRuleAIProvider()
    text = """Clinic visit\nDate: 2025-04-11\nHbA1c: 7.2%\nNo known allergies.\nStarted Metformin 500 mg."""

    result = await provider.extract_events(text, "CONSULTATION")

    types = {event["event_type"] for event in result.events}
    assert {"CONSULTATION", "TEST_RESULT", "ALLERGY_STATUS_REPORTED", "MEDICATION_STARTED"} <= types
    lab = next(event for event in result.events if event["event_type"] == "TEST_RESULT")
    assert lab["value"] == "7.2"
    assert lab["unit"] == "%"
    assert lab["event_date"] == "2025-04-11"
    assert lab["source_excerpt"] == "HbA1c: 7.2%"


@pytest.mark.asyncio
async def test_relative_dates_are_not_fabricated():
    provider = LocalRuleAIProvider()
    result = await provider.extract_events("Follow-up in 2 weeks.", "CONSULTATION")

    assert result.events
    assert result.events[0]["event_date"] is None


def test_explicit_date_parser_rejects_missing_date():
    assert parse_explicit_date("No date stated") is None


def test_explicit_date_parser_supports_day_month_year():
    assert parse_explicit_date("Date 10 January 2024") == "2024-01-10"


@pytest.mark.asyncio
async def test_ignores_unknown_allergy_and_trims_medication_stop_reason():
    provider = LocalRuleAIProvider()
    result = await provider.extract_events(
        "Allergies: Not documented in this visit.\nDiscontinue Metformin immediately due to side effects.",
        "CONSULTATION",
    )
    assert not any(event["event_type"] == "ALLERGY_REPORTED" for event in result.events)
    stopped = next(event for event in result.events if event["event_type"] == "MEDICATION_STOPPED")
    assert stopped["entity_name"] == "Metformin"
