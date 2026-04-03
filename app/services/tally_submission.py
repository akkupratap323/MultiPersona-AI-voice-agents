"""
Tally.so form submission service for appointment booking.

Uses the public widget endpoint (same as browser/embed):
  POST https://tally.so/api/forms/{formId}/respond
No API key required — identical to how the embedded form submits.
"""

import uuid
import httpx
from loguru import logger
from typing import Optional, Dict, Any


class TallySubmissionService:
    """Service for submitting appointment bookings to Tally.so"""

    def __init__(self):
        self.form_id = "eqe11o"
        # Public embed endpoint — no auth needed
        self.submission_endpoint = f"https://tally.so/api/forms/{self.form_id}/respond"

        # groupUuid values (NOT block uuids) — these are the correct response keys
        self.field_ids = {
            "first_name":   "f9fdb3ab-8281-48e2-85aa-19b9a251af54",
            "last_name":    "5bcb2e18-3723-4221-b8d3-1d35afceb363",
            "email":        "a4d47c9e-7b51-4f53-96aa-28e34c3edfa1",
            "submitted_by": "22ace3dc-fa1b-4630-8747-3075d26a58f1",
        }

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
                follow_redirects=True
            )
        return self._client

    async def submit_appointment(
        self,
        first_name: str,
        last_name: str,
        email: str
    ) -> Dict[str, Any]:
        """Submit appointment booking via Tally's public embed endpoint."""
        try:
            client = await self._get_client()

            # Payload mirrors what the Tally embed widget sends in the browser
            payload = {
                "sessionUuid":   str(uuid.uuid4()),
                "respondentUuid": str(uuid.uuid4()),
                "responses": {
                    self.field_ids["first_name"]:   first_name,
                    self.field_ids["last_name"]:    last_name,
                    self.field_ids["email"]:        email,
                    self.field_ids["submitted_by"]: "Voice AI",
                },
                "isCompleted": True,
                "captchas": {},
                "password": None,
            }

            logger.info(f"Submitting appointment to Tally.so for {first_name} {last_name} ({email})")

            response = await client.post(
                self.submission_endpoint,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Origin": "https://tally.so",
                    "Referer": f"https://tally.so/r/{self.form_id}",
                }
            )

            response.raise_for_status()

            data = response.json()
            logger.info(f"Tally.so submission successful: submissionId={data.get('submissionId')} for {email}")

            return {
                "success": True,
                "message": "We've received your request! Someone from our team will reach out to you shortly."
            }

        except httpx.TimeoutException:
            logger.error("Tally.so submission timeout")
            return {
                "success": False,
                "error": "I'm having trouble submitting the form right now. Could you try again in a moment?"
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Tally.so HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return {
                "success": False,
                "error": "Something went wrong with the booking. Let me try that again."
            }

        except Exception as e:
            logger.error(f"Tally.so submission error: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": "I encountered an error while submitting. Please try again or contact us directly."
            }

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
