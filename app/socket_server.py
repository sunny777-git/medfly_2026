# app/socket_server.py

import os

import uvicorn
from socketio import ASGIApp

from app.routers import webrtc_signaling


# Use the existing Socket.IO server from your webrtc_signaling router
sio = webrtc_signaling.sio

# ASGI app that serves only Socket.IO
sio_app = ASGIApp(sio)


def run_sio():
    """
    Entry point for `poetry run start-sio`.

    Runs the Socket.IO signaling server on a separate port
    from the FastAPI HTTP API.
    """
    uvicorn.run(
        "app.socket_server:sio_app",
        host="0.0.0.0",
        port=int(os.getenv("SIO_PORT", "9000")),
        reload=True,  # nice for development
    )


if __name__ == "__main__":
    run_sio()
