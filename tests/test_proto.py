"""Day 2, part B: Protocol Buffers.

First generate the Python code from the .proto file (run from the project root):
    python -m grpc_tools.protoc -I proto --python_out=src/digital_key proto/unlock.proto
This creates src/digital_key/unlock_pb2.py. Never edit that file by hand.
"""

import json

import pytest

pb = pytest.importorskip("digital_key.unlock_pb2", reason="run the protoc command first")

from digital_key.validation import validate  # noqa: E402 (must come after importorskip)


def make_request():
    return pb.UnlockRequest(
        vehicle_id="R1S-001",
        key_id="PHONE-JASMIN",
        command=pb.UNLOCK,
        timestamp_ms=1790000000000,
    )


def test_round_trip_serialize_and_parse():
    original = make_request()

    data = original.SerializeToString()          # message -> bytes (what goes over the network)
    parsed = pb.UnlockRequest.FromString(data)   # bytes -> message (what the vehicle does)

    assert parsed == original
    assert parsed.command == pb.UNLOCK


def test_protobuf_is_smaller_than_json():
    msg = make_request()
    as_json = json.dumps({
        "vehicle_id": msg.vehicle_id, "key_id": msg.key_id,
        "command": "UNLOCK", "timestamp_ms": msg.timestamp_ms,
    }).encode()

    print(f"\nprotobuf: {len(msg.SerializeToString())} bytes, JSON: {len(as_json)} bytes")
    assert len(msg.SerializeToString()) < len(as_json)


def test_unset_fields_get_default_values():
    # proto3 has no "missing": unset fields get defaults (empty string, 0, first enum value)
    msg = pb.UnlockRequest(vehicle_id="R1S-001")

    assert msg.key_id == ""
    assert msg.timestamp_ms == 0
    assert msg.command == pb.COMMAND_UNSPECIFIED


def test_garbage_bytes_are_rejected():
    from google.protobuf.message import DecodeError

    with pytest.raises(DecodeError):
        pb.UnlockRequest.FromString(b"\xff\xff\xff not a protobuf")


# EXERCISE: a vehicle must reject a request with no command.
# Write a function validate(request) that raises ValueError when
# request.command == pb.COMMAND_UNSPECIFIED or key_id is empty,
# and write two tests for it (one valid, one invalid).
# As a tester: why is it dangerous that proto3 silently fills in defaults?
def test_valid_request():
    validate(make_request())


def test_request_without_command_is_rejected():
    msg = pb.UnlockRequest(vehicle_id="R1S-001", key_id="PHONE-JASMIN")  # no command

    with pytest.raises(ValueError, match="command"):
        validate(msg)


def test_request_without_key_id_is_rejected():
    msg = pb.UnlockRequest(vehicle_id="R1S-001", command=pb.UNLOCK)  # no command

    with pytest.raises(ValueError, match="key_id"):
        validate(msg)