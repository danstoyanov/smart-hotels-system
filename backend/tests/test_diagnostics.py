"""Failure evidence through the real SDK/ADK boundary with no network or real ADC."""

import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from google import genai
from google.adk.models import Gemini
from google.auth.credentials import AnonymousCredentials
from google.genai import types

from backend import smoke
from backend.app.agent import generate_reply
from backend.app.diagnostics import AssistantFailure, InvocationDiagnostics
from backend.app.hotel import HotelStore
from backend.app.settings import Settings


def test_real_sdk_stream_timeout_retry_and_failure_evidence(monkeypatch):
    assert "client" in Gemini.model_fields
    requests = []

    def transport(request):
        requests.append(request)
        assert request.url.host == "aiplatform.googleapis.com"
        assert "/v1/projects/offline/locations/global/" in request.url.path
        assert request.url.path.endswith("gemini-3.8-flash:streamGenerateContent")
        assert request.url.params["alt"] == "sse"
        assert request.headers["x-server-timeout"] == "60"
        assert set(request.extensions["timeout"].values()) == {60.0}
        payload = json.loads(request.content)
        assert payload["generationConfig"]["maxOutputTokens"] == 2048
        # The installed SDK preserves snake_case keys inside ThinkingConfig.
        assert payload["generationConfig"]["thinkingConfig"] == {"thinking_level": "LOW"}
        if len(requests) == 1:
            data = {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "read_information",
                                        "args": {"section": "policies", "item_id": "arrival"},
                                    }
                                }
                            ],
                        },
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 20,
                    "candidatesTokenCount": 4,
                    "totalTokenCount": 24,
                },
            }
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                text=f"data: {json.dumps(data)}\n\n",
            )
        raise httpx.ReadTimeout("SECRET provider text", request=request)

    original = genai.Client
    credentials = AnonymousCredentials()
    credentials.token = "offline-test-token"

    def client_factory(**kwargs):
        # Preserve the production project, endpoint, API version, timeout and retries.
        options = kwargs["http_options"]
        options.client_args = {
            **(options.client_args or {}),
            "transport": httpx.MockTransport(transport),
        }
        options.async_client_args = {
            **(options.async_client_args or {}),
            "transport": httpx.MockTransport(transport),
        }
        options.httpx_async_client = httpx.AsyncClient(
            transport=httpx.MockTransport(transport),
            event_hooks=options.httpx_async_client.event_hooks,
        )
        return original(**kwargs, credentials=credentials)

    monkeypatch.setattr(genai, "Client", client_factory)
    hotel = HotelStore()
    hotel.reload()
    with pytest.raises(AssistantFailure) as caught:
        asyncio.run(
            generate_reply(
                Settings(
                    _env_file=None,
                    assistant_mode="vertex",
                    google_cloud_project="offline",
                    google_cloud_location="global",
                ),
                hotel,
                "privateguestquestion",
                http_transport="httpx",
            )
        )
    diagnostic = caught.value.diagnostics
    assert len(requests) == 2  # No retry of the failed second request.
    assert diagnostic["model_calls_attempted"] == 2
    assert diagnostic["tool_steps"] == [
        {"name": "read_information", "model_call": 1, "completed": True}
    ]
    assert diagnostic["failure"]["status"] == "HTTP_READ_TIMEOUT"
    assert diagnostic["failure"]["phase"] == "model"
    assert diagnostic["reported_usage"]["total_tokens"] == 24
    assert diagnostic["usage_complete"] is False
    assert diagnostic["cost_usd"] is None
    assert diagnostic["elapsed_seconds"] >= 0
    shapes = [event for event in diagnostic["events"] if event["kind"] == "http_request"]
    assert len(shapes) == 2
    assert shapes[1]["functions"][-1] == {"kind": "functionResponse", "name": "read_information"}
    assert shapes[1]["bytes"] > shapes[0]["bytes"]
    assert "SECRET" not in json.dumps(diagnostic)
    assert "privateguestquestion" not in json.dumps(diagnostic)
    assert "Authorization" not in json.dumps(diagnostic)


def test_partial_usage_monotonic_timing_and_safe_provider_status():
    now = [10.0]
    diagnostic = InvocationDiagnostics(clock=lambda: now[0])
    diagnostic.before_model(None, None)
    now[0] = 11.0
    metadata = types.GenerateContentResponseUsageMetadata(total_token_count=8)
    diagnostic.after_model(None, SimpleNamespace(partial=True, usage_metadata=metadata))
    diagnostic.after_model(None, SimpleNamespace(partial=True, usage_metadata=metadata))
    error = RuntimeError("SECRET")
    error.code = 429
    diagnostic.fail(error)
    result = diagnostic.finish()
    assert result["elapsed_seconds"] == 1.0
    assert result["reported_usage"]["total_tokens"] == 8
    assert result["usage_complete"] is False
    assert result["failure"]["status"] == "RESOURCE_EXHAUSTED"
    assert result["failure"]["http_code"] == 429
    assert "SECRET" not in json.dumps(result)
    unknown = InvocationDiagnostics().finish()
    assert unknown["reported_usage"]["total_tokens"] is None


def test_smoke_failure_persists_evidence_and_stops(monkeypatch, tmp_path):
    settings = Settings(
        _env_file=None,
        assistant_mode="vertex",
        google_cloud_project="offline",
        google_cloud_location="global",
    )
    monkeypatch.setattr(smoke, "Settings", lambda: settings)
    called = []

    async def broken(*args):
        called.append(True)
        diagnostic = InvocationDiagnostics()
        diagnostic.before_model(None, None)
        diagnostic.fail(httpx.ReadTimeout("SECRET"))
        raise AssistantFailure(diagnostic.finish())

    monkeypatch.setattr(smoke, "generate_reply", broken)
    output = tmp_path / "report.json"
    with pytest.raises(SystemExit, match="safe report saved"):
        asyncio.run(smoke.run(SimpleNamespace(approved_paid_calls=True, case=None, output=output)))
    report = json.loads(output.read_text(encoding="utf-8"))
    assert len(called) == 1
    assert report["failure"]["case"] == "arrival"
    assert report["failure"]["diagnostics"]["failure"]["status"] == "HTTP_READ_TIMEOUT"
    assert report["failure"]["diagnostics"]["reported_usage"]["total_tokens"] is None
    assert report["results"] == []
    assert "SECRET" not in output.read_text(encoding="utf-8")


def test_two_sdk_transports_same_payload_and_no_retry(monkeypatch):
    from datetime import date

    import aiohttp

    original = genai.Client
    credentials = AnonymousCredentials()
    credentials.token = "offline-test-token"
    payloads, diagnostics = {}, {}
    sends = []

    def httpx_request(request):
        sends.append("httpx")
        assert request.method.lower() == "post"
        assert "/v1/projects/offline/locations/global/" in request.url.path
        assert set(request.extensions["timeout"].values()) == {60.0}
        payloads["httpx"] = json.loads(request.content)
        raise httpx.ReadTimeout("SECRET HTTPX timeout", request=request)

    async def aiohttp_request(self, method, url, **kwargs):
        sends.append("aiohttp")
        # SDK supplies lowercase 'post'; HTTP methods are case-insensitive here.
        assert method.lower() == "post"
        assert "/v1/projects/offline/locations/global/" in url
        assert kwargs["timeout"].total == 60
        payloads["aiohttp"] = json.loads(kwargs["data"])
        raise TimeoutError("SECRET aiohttp timeout")

    def client_factory(**kwargs):
        options = kwargs["http_options"]
        if options.httpx_async_client is not None:
            options.httpx_async_client = httpx.AsyncClient(
                transport=httpx.MockTransport(httpx_request),
                event_hooks=options.httpx_async_client.event_hooks,
            )
        return original(**kwargs, credentials=credentials)

    monkeypatch.setattr(genai, "Client", client_factory)
    monkeypatch.setattr(aiohttp.ClientSession, "_request", aiohttp_request)
    hotel = HotelStore()
    hotel.reload()
    settings = Settings(
        _env_file=None,
        assistant_mode="vertex",
        google_cloud_project="offline",
        google_cloud_location="global",
    )
    for transport in ("httpx", "aiohttp"):
        with pytest.raises(AssistantFailure) as caught:
            asyncio.run(
                generate_reply(
                    settings,
                    hotel,
                    "Is breakfast included and when is it served?",
                    http_transport=transport,
                    max_model_calls=2,
                    property_date=date(2026, 10, 24),
                )
            )
        diagnostics[transport] = caught.value.diagnostics
    assert sends == ["httpx", "aiohttp"]  # One attempt each, including SDK retries.
    assert payloads["httpx"] == payloads["aiohttp"]
    assert diagnostics["httpx"]["failure"]["status"] == "HTTP_READ_TIMEOUT"
    assert diagnostics["aiohttp"]["failure"]["status"] == "MODEL_TIMEOUT"
    assert (
        diagnostics["httpx"]["model_calls"][0]["request_sha256"]
        == diagnostics["aiohttp"]["model_calls"][0]["request_sha256"]
    )
    for result in diagnostics.values():
        assert result["model_calls_attempted"] == 1
        assert result["failure"]["phase"] == "model"
        assert result["reported_usage"]["total_tokens"] is None
        assert result["usage_complete"] is False
        assert result["cost_usd"] is None
        assert "SECRET" not in json.dumps(result)
    deadline = InvocationDiagnostics()
    deadline.fail(TimeoutError("SECRET application deadline"))
    assert deadline.finish()["failure"]["status"] == "APPLICATION_TIMEOUT"


def test_transport_comparison_requires_opt_in_and_runs_only_one_pair(monkeypatch, tmp_path):
    from backend.app.agent import Reply

    settings = Settings(
        _env_file=None,
        assistant_mode="vertex",
        google_cloud_project="offline",
        google_cloud_location="global",
    )
    monkeypatch.setattr(smoke, "Settings", lambda: settings)
    called = []

    async def fake_reply(actual_settings, hotel, question, **kwargs):
        called.append((actual_settings, hotel, question, kwargs))
        diagnostic = InvocationDiagnostics()
        diagnostic.before_model(None, None)
        diagnostic.calls[0]["request_sha256"] = "same-fixed-input"
        if kwargs["http_transport"] == "httpx":
            diagnostic.fail(httpx.ReadTimeout("SECRET"))
            raise AssistantFailure(diagnostic.finish())
        diagnostic.phase = "completed"
        return Reply("offline fixture", diagnostics=diagnostic.finish())

    monkeypatch.setattr(smoke, "generate_reply", fake_reply)
    args = SimpleNamespace(
        approved_paid_calls=False,
        compare_transports=True,
        case="breakfast",
        output=tmp_path / "pair.json",
    )
    with pytest.raises(SystemExit, match="approved-paid-calls"):
        asyncio.run(smoke.run(args))
    assert called == []
    args.approved_paid_calls = True
    asyncio.run(smoke.run(args))
    assert len(called) == 2
    assert called[0][:3] == called[1][:3]
    assert called[0][3]["property_date"] == called[1][3]["property_date"]
    assert [call[3]["http_transport"] for call in called] == ["httpx", "aiohttp"]
    assert all(call[3]["max_model_calls"] == 2 for call in called)
    report = json.loads(args.output.read_text(encoding="utf-8"))
    assert [row["outcome"] for row in report["results"]] == ["failed", "completed"]
    assert report["same_first_model_request"] is True
    assert report["automatic_retries"] is False
    assert report["live_complete"] is False
