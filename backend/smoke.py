"""Explicit opt-in live checks. No automatic retries or model-based grading."""

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from backend.app.agent import generate_reply
from backend.app.hotel import HotelStore
from backend.app.runtime import new_loop
from backend.app.settings import ROOT, Settings


async def run(args):
    settings = Settings()
    if not args.approved_paid_calls or settings.assistant_mode != "vertex":
        raise SystemExit("Set Vertex settings and pass --approved-paid-calls after budget approval")
    hotel = HotelStore(
        expected_hotel=(settings.hotel_name, settings.hotel_language, settings.hotel_timezone)
    )
    hotel.reload()
    cases = json.loads((ROOT / "evals/assistant-smoke.json").read_text(encoding="utf-8"))
    selected = [case for case in cases if not args.case or case["id"] == args.case]
    if not selected:
        raise SystemExit("Unknown case")
    report = {"model": settings.gemini_model, "results": [], "live_complete": False}
    for case in selected:
        try:
            reply = await generate_reply(settings, hotel, case["question"])
        except Exception as exc:
            report["failure"] = {"case": case["id"], "type": type(exc).__name__}
            args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
            raise SystemExit("Live check failed; safe report saved. No retry was made.") from None
        report["results"].append({**case, **asdict(reply), "reviewed": False})
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {len(selected)} live answers. Review each answer before claiming acceptance.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-paid-calls", action="store_true")
    parser.add_argument("--case", choices=["arrival", "breakfast", "unknown", "booking"])
    parser.add_argument("--output", type=Path, default=Path("assistant-smoke.local.json"))
    asyncio.run(run(parser.parse_args()), loop_factory=new_loop)


if __name__ == "__main__":
    main()
