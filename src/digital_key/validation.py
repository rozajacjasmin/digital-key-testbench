from . import unlock_pb2 as pb


def validate(request: pb.UnlockRequest) -> None:
    """Raise ValueError if the request is missing a key_id or a command."""
    if not request.key_id:
        raise ValueError("key_id is required")
    if request.command == pb.COMMAND_UNSPECIFIED:
        raise ValueError("command is required")
