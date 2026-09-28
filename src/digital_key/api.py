"""Day 2: a small REST API ("key server") on top of KeyManager.

Run it locally:
    uvicorn digital_key.api:app --reload --app-dir src
Then open http://127.0.0.1:8000/docs to see and try every endpoint.

Every endpoint except /health needs the header:  X-API-Token: test-token
"""

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel

from .key_manager import KeyError_, KeyManager, UnlockResult

API_TOKEN = "test-token"


# --- Request / response models (the JSON "shapes") --------------------------
class KeyCreate(BaseModel):
    key_id: str
    vehicle_id: str
    owner: str
    valid_days: int = 365


class KeyOut(BaseModel):
    key_id: str
    vehicle_id: str
    owner: str
    revoked: bool


class CommandIn(BaseModel):
    key_id: str
    command: str = "unlock"


class CommandOut(BaseModel):
    vehicle_id: str
    command: str
    result: UnlockResult


def create_app() -> FastAPI:
    """Build a fresh app with its own empty KeyManager.
    Tests call this so every test starts from a clean state."""
    app = FastAPI(title="Digital Key Server")
    manager = KeyManager()

    def check_token(x_api_token: str | None = Header(default=None)):
        if x_api_token != API_TOKEN:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or missing API token")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/keys", status_code=201, response_model=KeyOut, dependencies=[Depends(check_token)])
    def register_key(body: KeyCreate):
        try:
            key = manager.register(body.key_id, body.vehicle_id, body.owner, body.valid_days)
        except KeyError_ as e:
            code = 409 if "already registered" in str(e) else 400
            raise HTTPException(code, str(e))
        return KeyOut(key_id=key.key_id, vehicle_id=key.vehicle_id, owner=key.owner, revoked=key.revoked)

    @app.delete("/keys/{key_id}", status_code=204, dependencies=[Depends(check_token)])
    def revoke_key(key_id: str):
        try:
            manager.revoke(key_id)
        except KeyError_ as e:
            raise HTTPException(404, str(e))
        return Response(status_code=204)

    @app.get("/vehicles/{vehicle_id}/keys", response_model=list[KeyOut], dependencies=[Depends(check_token)])
    def list_keys(vehicle_id: str):
        return [
            KeyOut(key_id=k.key_id, vehicle_id=k.vehicle_id, owner=k.owner, revoked=k.revoked)
            for k in manager.keys_for_vehicle(vehicle_id)
        ]

    @app.post("/vehicles/{vehicle_id}/commands", response_model=CommandOut, dependencies=[Depends(check_token)])
    def send_command(vehicle_id: str, body: CommandIn, response: Response):
        try:
            result = manager.authorize(body.key_id, vehicle_id, body.command)
        except KeyError_ as e:
            raise HTTPException(400, str(e))
        if result != UnlockResult.GRANTED:
            response.status_code = 403
        return CommandOut(vehicle_id=vehicle_id, command=body.command, result=result)

    return app


app = create_app()
