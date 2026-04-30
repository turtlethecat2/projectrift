from api.schemas import EventPayload


def test_event_payload_accepts_valid_event():
    p = EventPayload(
        source="manual",
        event_type="call_dial",
        metadata={"x": 1},
    )
    assert p.source == "manual"
