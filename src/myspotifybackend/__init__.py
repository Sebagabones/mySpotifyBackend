import os

import uvicorn

from myspotifybackend.main import Application


def main() -> None:
    uvicorn.run(
        "myspotifybackend.main:Application",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "")),
        reload=True,
        factory=True,
    )
