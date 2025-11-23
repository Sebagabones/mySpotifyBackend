import os

import uvicorn

from myspotifybackend.main import app


def main() -> None:
    uvicorn.run(
        # "myspotifybackend.main:app",
        "myspotifybackend.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "")),
        # reload=True,
    )
