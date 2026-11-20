"""
Unit tests for the Tally.so appointment submission service.

No network: the service's HTTP client is swapped for one with an httpx.MockTransport.
"""

import json

import httpx
import pytest

from app.services.tally_submission import TallySubmissionService


def _service(handler):
    """A service whose requests go to ``handler`` instead of tally.so."""
    service = TallySubmissionService()
    service.requests = []

    def record(request):
        service.requests.append(request)
        return handler(request)

    service._client = httpx.AsyncClient(transport=httpx.MockTransport(record))
    return service


async def _submit(service):
    try:
        return await service.submit_appointment("Ada", "Lovelace", "ada@example.com")
    finally:
        await service.close()


class TestSuccess:
    """A 2xx reply is a stored booking, whatever its body."""

    async def test_a_json_reply_is_a_success(self):
        service = _service(lambda request: httpx.Response(200, json={"submissionId": "s1"}))

        result = await _submit(service)

        assert result["success"] is True
        assert "received your request" in result["message"]

    @pytest.mark.parametrize(
        "reply",
        [
            httpx.Response(200, content=b""),
            httpx.Response(200, text="<html>Thanks!</html>"),
            httpx.Response(200, json=["s1"]),
            httpx.Response(200, json="ok"),
            httpx.Response(204),
        ],
        ids=["empty", "html", "json-list", "json-string", "no-content"],
    )
    async def test_a_body_that_is_not_a_json_object_is_still_a_success(self, reply):
        service = _service(lambda request: reply)

        result = await _submit(service)

        assert result["success"] is True
        assert "error" not in result
        assert len(service.requests) == 1

    async def test_the_answers_are_sent_under_the_form_field_ids(self):
        service = _service(lambda request: httpx.Response(200, json={"submissionId": "s1"}))

        await _submit(service)

        (request,) = service.requests
        assert request.method == "POST"
        assert str(request.url) == "https://tally.so/api/forms/eqe11o/respond"
        responses = json.loads(request.content)["responses"]
        assert responses[service.field_ids["first_name"]] == "Ada"
        assert responses[service.field_ids["last_name"]] == "Lovelace"
        assert responses[service.field_ids["email"]] == "ada@example.com"


class TestFailure:
    """A reply that is not 2xx, or no reply, is a failure the user can retry."""

    @pytest.mark.parametrize("status", [400, 429, 500, 503])
    async def test_an_error_status_is_a_failure(self, status):
        service = _service(lambda request: httpx.Response(status, json={"error": "nope"}))

        result = await _submit(service)

        assert result["success"] is False
        assert result["error"] == "Something went wrong with the booking. Let me try that again."

    async def test_a_timeout_is_a_failure(self):
        def handler(request):
            raise httpx.ReadTimeout("slow", request=request)

        result = await _submit(_service(handler))

        assert result["success"] is False
        assert "trouble submitting" in result["error"]

    async def test_a_connection_error_is_a_failure(self):
        def handler(request):
            raise httpx.ConnectError("down", request=request)

        result = await _submit(_service(handler))

        assert result["success"] is False
        assert "error while submitting" in result["error"]
