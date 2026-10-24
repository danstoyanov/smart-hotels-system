"""Safe invocation metadata only: no prompts, answers, arguments or credentials."""

import hashlib
import json
from copy import deepcopy
from time import monotonic

STATUSES = {
    400: "INVALID_ARGUMENT",
    401: "UNAUTHENTICATED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    408: "DEADLINE_EXCEEDED",
    429: "RESOURCE_EXHAUSTED",
    500: "INTERNAL",
    502: "UNAVAILABLE",
    503: "UNAVAILABLE",
    504: "DEADLINE_EXCEEDED",
}
CATEGORIES = {
    "ReadTimeout",
    "ConnectTimeout",
    "WriteTimeout",
    "PoolTimeout",
    "TimeoutError",
    "ConnectError",
    "ReadError",
    "ServerError",
    "ClientError",
    "RuntimeError",
    "ValueError",
    "LlmCallsLimitExceededError",
    "CancelledError",
}
TOKEN_FIELDS = {
    "input_tokens": "prompt_token_count",
    "output_tokens": "candidates_token_count",
    "thinking_tokens": "thoughts_token_count",
    "total_tokens": "total_token_count",
}


class AssistantFailure(RuntimeError):
    def __init__(self, diagnostics):
        self.diagnostics = diagnostics
        super().__init__("Assistant invocation failed")


class InvocationDiagnostics:
    def __init__(self, *, clock=monotonic):
        self.clock, self.started = clock, clock()
        self.phase = "setup"
        self.calls = []
        self.tools = []
        self.events = []
        self.failure = None

    def elapsed(self):
        return round(self.clock() - self.started, 3)

    def record(self, kind, **fields):
        self.events.append({"kind": kind, "elapsed_seconds": self.elapsed(), **fields})

    async def before_http_request(self, request):
        # Inspect shape only. Never retain request text, arguments, headers or URLs.
        try:
            payload = json.loads(request.content)
            contents = payload.get("contents", [])
            parts = [part for content in contents for part in content.get("parts", [])]
            functions = []
            for part in parts:
                for kind in ("functionCall", "functionResponse"):
                    if kind in part:
                        name = part[kind].get("name")
                        functions.append(
                            {
                                "kind": kind,
                                "name": name
                                if name in {"list_information", "read_information"}
                                else "other",
                            }
                        )
            self.record(
                "http_request",
                model_call=len(self.calls),
                bytes=len(request.content),
                contents=len(contents),
                parts=len(parts),
                roles=[
                    content.get("role")
                    if content.get("role") in {"user", "model", "tool"}
                    else "other"
                    for content in contents
                ],
                functions=functions,
            )
        except (ValueError, TypeError, KeyError):
            self.record("http_request_shape_unavailable", model_call=len(self.calls))

    async def after_http_response(self, response):
        self.record(
            "http_response_headers", model_call=len(self.calls), http_code=response.status_code
        )

    def before_model(self, callback_context, llm_request):
        self.phase = "model"
        fingerprint = None
        if llm_request is not None:
            # Compare model inputs without saving prompt text or credentials.
            payload = {
                "model": llm_request.model,
                "contents": [item.model_dump(mode="json") for item in llm_request.contents],
                "config": llm_request.config.model_dump(mode="json", exclude={"http_options"}),
            }
            fingerprint = hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode("utf-8")
            ).hexdigest()
        self.calls.append(
            {
                "number": len(self.calls) + 1,
                "started_seconds": self.elapsed(),
                "completed": False,
                "reported_usage": None,
                "request_sha256": fingerprint,
            }
        )
        self.record("model_started", model_call=len(self.calls))

    def after_model(self, callback_context, llm_response):
        call = self.calls[-1]
        if "first_response_seconds" not in call:
            call["first_response_seconds"] = self.elapsed()
        metadata = llm_response.usage_metadata
        if metadata:
            # Streaming usage is cumulative within one model call. Do not add chunks twice.
            usage = call["reported_usage"] or {}
            for key, attr in TOKEN_FIELDS.items():
                value = getattr(metadata, attr, None)
                if type(value) is int:
                    usage[key] = max(usage.get(key, 0), value)
            call["reported_usage"] = usage or None
        if not llm_response.partial and not call["completed"]:
            call["completed"] = True
            call["duration_seconds"] = round(self.elapsed() - call["started_seconds"], 3)
            self.phase = "between_calls"
            self.record("model_completed", model_call=len(self.calls))

    def before_tool(self, tool, args, tool_context):
        self.phase = "tool"
        name = tool.name if tool.name in {"list_information", "read_information"} else "other"
        self.tools.append({"name": name, "model_call": len(self.calls), "completed": False})
        self.record("tool_started", tool=name, model_call=len(self.calls))

    def after_tool(self, tool, args, tool_context, tool_response):
        name = tool.name if tool.name in {"list_information", "read_information"} else "other"
        for step in reversed(self.tools):
            if step["name"] == name and not step["completed"]:
                step["completed"] = True
                break
        self.phase = "between_calls"
        self.record("tool_completed", tool=name, model_call=len(self.calls))

    def fail(self, error=None, *, status=None):
        if self.failure is not None:
            return
        causes, code, timed_out = [], None, False
        seen = set()
        while error is not None and id(error) not in seen and len(causes) < 5:
            seen.add(id(error))
            timed_out = timed_out or isinstance(error, TimeoutError)
            name = type(error).__name__
            causes.append(name if name in CATEGORIES else "Exception")
            candidate = getattr(error, "code", None)
            if type(candidate) is int and candidate in STATUSES:
                code = candidate
            error = error.__cause__ or error.__context__
        safe_status = STATUSES.get(code)
        if safe_status is None:
            safe_status = status if status in set(STATUSES.values()) else "ASSISTANT_ERROR"
            if "ReadTimeout" in causes:
                safe_status = "HTTP_READ_TIMEOUT"
            elif timed_out:
                safe_status = (
                    "MODEL_TIMEOUT" if status == "MODEL_TIMEOUT" else "APPLICATION_TIMEOUT"
                )
        self.failure = {
            "phase": self.phase,
            "category": causes[0] if causes else "ModelEventError",
            "causes": causes,
            "http_code": code,
            "status": safe_status,
        }
        self.record("failure", **self.failure)

    def on_model_error(self, callback_context, llm_request, error):
        self.fail(error, status="MODEL_TIMEOUT")

    def on_tool_error(self, tool, args, tool_context, error):
        self.fail(error)

    def finish(self):
        reported = [call["reported_usage"] for call in self.calls if call["reported_usage"]]
        usage = {
            key: sum(row[key] for row in reported if key in row)
            if any(key in row for row in reported)
            else None
            for key in TOKEN_FIELDS
        }
        return deepcopy(
            {
                "elapsed_seconds": self.elapsed(),
                "phase": self.phase,
                "model_calls_attempted": len(self.calls),
                "model_calls": self.calls,
                "tool_steps": self.tools,
                "events": self.events,
                "failure": self.failure,
                "reported_usage": usage,
                "usage_complete": bool(self.calls)
                and all(
                    call["completed"] and call["reported_usage"] is not None for call in self.calls
                ),
                "cost_usd": None,
            }
        )
