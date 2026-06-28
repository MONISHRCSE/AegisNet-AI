import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

TAIL_POLL_INTERVAL = 0.05  # seconds — 50ms polling for near-real-time ingestion


async def tail_file(path: str) -> AsyncGenerator[str, None]:
    """
    Async generator that continuously tails a file, yielding new lines as they appear.
    On startup, seeks to end-of-file so only new traffic is processed.
    Handles log rotation: detects file shrinkage and reopens from the start.
    """
    log_path = Path(path)

    # Wait for the file to be created (Zeek takes a moment to initialise)
    while not log_path.exists():
        await asyncio.sleep(1.0)

    with open(log_path, "r") as f:
        f.seek(0, 2)  # Seek to EOF — ignore pre-existing lines
        last_inode = os.fstat(f.fileno()).st_ino

        while True:
            line = f.readline()
            if line:
                yield line
            else:
                await asyncio.sleep(TAIL_POLL_INTERVAL)

                # ── Rotation / Truncation detection ──────────────────────
                try:
                    current_inode = log_path.stat().st_ino
                    current_size = log_path.stat().st_size
                except FileNotFoundError:
                    # File removed — wait for Zeek to recreate
                    await asyncio.sleep(2.0)
                    continue

                file_pos = f.tell()
                if current_inode != last_inode or current_size < file_pos:
                    # Zeek rotated or truncated the log
                    f.close()
                    f = open(log_path, "r")
                    last_inode = os.fstat(f.fileno()).st_ino
