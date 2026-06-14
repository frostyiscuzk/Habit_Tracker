"""Railway launcher for the single-service deployment.

This process starts the Telegram bot first, then starts Streamlit as a child
process. That is more reliable than starting the bot inside app.py because
Streamlit reruns app.py for dashboard sessions.
"""

from __future__ import annotations

import os
import subprocess
import sys

from .bot import start_bot_from_env_once


def main() -> int:
    """Start the optional Telegram bot and the Streamlit analytics dashboard."""

    start_bot_from_env_once()
    port = os.getenv("PORT", "8501")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.address",
        "0.0.0.0",
        "--server.port",
        port,
    ]
    process = subprocess.Popen(command)
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
