"""Explicit opt-in live checks. No automatic retries or model-based grading."""

import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from time import monotonic
from zoneinfo import ZoneInfo

from backend.app.agent import generate_reply
from backend.app.diagnostics import AssistantFailure, InvocationDiagnostics
from backend.app.hotel import HotelStore
from backend.app.runtime import new_loop
from backend.app.settings import ROOT, Settings


async def compare_transports(args, settings, hotel, cases):
    if args.case not in (None, "breakfast"):
        raise SystemExit("Transport comparison uses the fixed breakfast case only")
    question = next(case["question"] for case in cases if case["id"] == "breakfast")
    property_date = datetime.now(ZoneInfo(settings.hotel_timezone)).date()
    report = {
        "model": settings.gemini_model,
        "project": settings.google_cloud_project,
        "location": settings.google_cloud_location,
        "api_version": "v1",
        "question": question,
        "property_date": property_date.isoformat(),
        "max_agent_runs": 2,
        "max_model_calls_per_run": 2,
        "automatic_retries": False,
        "live_complete": False,
        "results": [],
    }
    for transport in ("httpx", "aiohttp"):
        row = {"transport": transport, "outcome": "started"}
        report["results"].append(row)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        started = monotonic()
        try:
            reply = await generate_reply(
                settings,
                hotel,
                question,
                http_transport=transport,
                max_model_calls=2,
                property_date=property_date,
            )
            row.update(outcome="completed", **asdict(reply), reviewed=False)
        except AssistantFailure as exc:
            row.update(outcome="failed", diagnostics=exc.diagnostics)
        except Exception as exc:
            diagnostic = InvocationDiagnostics()
            diagnostic.fail(exc)
            row.update(outcome="failed", diagnostics=diagnostic.finish())
        row["wall_elapsed_seconds"] = round(monotonic() - started, 3)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    fingerprints = [
        row.get("diagnostics", {}).get("model_calls", [{}])[0].get("request_sha256")
        if row.get("diagnostics", {}).get("model_calls")
        else None
        for row in report["results"]
    ]
    report["same_first_model_request"] = (
        fingerprints[0] == fingerprints[1] if all(fingerprints) else None
    )
    report["conclusion"] = "Review this one pair; it cannot establish a reliable timeout fix."
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Saved exactly two transport runs. No automatic retries or model grading.")


async def run(args):
    settings = Settings()
    if not args.approved_paid_calls or settings.assistant_mode != "vertex":
        raise SystemExit("Set Vertex settings and pass --approved-paid-calls after budget approval")
    hotel = HotelStore(
        expected_hotel=(settings.hotel_name, settings.hotel_language, settings.hotel_timezone)
    )
    hotel.reload()
    cases = json.loads((ROOT / "evals/assistant-smoke.json").read_text(encoding="utf-8"))
    if getattr(args, "compare_transports", False):
        return await compare_transports(args, settings, hotel, cases)
    selected = [case for case in cases if not args.case or case["id"] == args.case]
    if not selected:
        raise SystemExit("Unknown case")
    report = {"model": settings.gemini_model, "results": [], "live_complete": False}
    for case in selected:
        diagnostic = InvocationDiagnostics()
        try:
            reply = await generate_reply(settings, hotel, case["question"])
        except Exception as exc:
            if isinstance(exc, AssistantFailure):
                details = exc.diagnostics
            else:
                diagnostic.fail(exc)
                details = diagnostic.finish()
            report["failure"] = {"case": case["id"], "diagnostics": details}
            args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
            raise SystemExit("Live check failed; safe report saved. No retry was made.") from None
        report["results"].append({**case, **asdict(reply), "reviewed": False})
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {len(selected)} live answers. Review each answer before claiming acceptance.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-paid-calls", action="store_true")
    parser.add_argument("--compare-transports", action="store_true")
    parser.add_argument("--case", choices=["arrival", "breakfast", "unknown", "booking"])
    parser.add_argument("--output", type=Path, default=Path("assistant-smoke.local.json"))
    asyncio.run(run(parser.parse_args()), loop_factory=new_loop)


if __name__ == "__main__":
    main()
