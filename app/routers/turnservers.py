from fastapi import APIRouter

router = APIRouter()

@router.get("/turnservers")
async def get_turn_servers():
    return {
        "iceServers": [
            { "urls": "stun:stun.l.google.com:19302" },
            { "urls": "turn:your.turn.server:3478", "username": "user", "credential": "pass" }
        ]
    }