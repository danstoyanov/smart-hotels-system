import asyncio
import selectors
import sys


def new_loop() -> asyncio.AbstractEventLoop:
    """Psycopg needs a selector event loop on Windows."""
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop(selectors.SelectSelector())
    return asyncio.new_event_loop()
