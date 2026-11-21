"""Function-call handlers of ConversationManager with arguments a model really sends.

The handlers are called on a stand-in ``self`` that has only what they read, so no LLM, TTS
or network service is created.
"""

from types import SimpleNamespace

import pytest

from app.services.conversation import ConversationManager, _text_argument

EMAIL_AGAIN = "That email doesn't look quite right. Could you please spell it out again slowly?"
NAMES_AGAIN = "I need both your first and last name. Could you provide those?"


class _Tally:
    def __init__(self):
        self.calls = []

    async def submit_appointment(self, **kwargs):
        self.calls.append(kwargs)
        return {"success": True, "message": "Booked."}


def _params(arguments):
    results = []

    async def result_callback(result, *args, **kwargs):
        results.append(result)

    return SimpleNamespace(arguments=arguments, result_callback=result_callback), results


async def _submit(arguments):
    manager = SimpleNamespace(tally_service=_Tally(), _booking_in_progress=True)
    params, results = _params(arguments)
    await ConversationManager._handle_submit_appointment(manager, params)
    return manager, results


class TestTextArgument:
    @pytest.mark.parametrize(
        "arguments, expected",
        [
            ({"email": "  a@b.com "}, "a@b.com"),
            ({"email": None}, ""),
            ({"email": 42}, ""),
            ({"email": ["a@b.com"]}, ""),
            ({}, ""),
            (None, ""),
        ],
    )
    def test_only_text_is_kept(self, arguments, expected):
        assert _text_argument(arguments, "email") == expected


class TestSubmitAppointment:
    @pytest.mark.asyncio
    async def test_a_null_email_asks_for_it_again(self):
        manager, results = await _submit(
            {"first_name": "Ada", "last_name": "Lovelace", "email": None}
        )

        assert results == [EMAIL_AGAIN]
        assert manager.tally_service.calls == []
        assert manager._booking_in_progress is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("field", ["first_name", "last_name"])
    async def test_a_null_name_asks_for_both_names(self, field):
        arguments = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
        arguments[field] = None

        manager, results = await _submit(arguments)

        assert results == [NAMES_AGAIN]
        assert manager.tally_service.calls == []

    @pytest.mark.asyncio
    async def test_a_number_for_a_name_asks_for_both_names(self):
        manager, results = await _submit(
            {"first_name": 7, "last_name": "Lovelace", "email": "ada@example.com"}
        )

        assert results == [NAMES_AGAIN]
        assert manager.tally_service.calls == []

    @pytest.mark.asyncio
    async def test_complete_details_are_submitted(self):
        """Control: the same handler submits when every field is text."""
        manager, results = await _submit(
            {"first_name": " Ada ", "last_name": "Lovelace", "email": "ada@example.com"}
        )

        assert results == ["Booked."]
        assert manager.tally_service.calls == [
            {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
        ]
        assert manager._booking_in_progress is False


class TestTransferToAgent:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("agent_id", [None, 3])
    async def test_an_agent_id_that_is_not_text_names_the_agents(self, agent_id):
        manager = SimpleNamespace(
            personas_config={"agents": {"sales": {"name": "Sam"}, "ops": {"name": "Olu"}}},
            current_persona_id="sales",
        )
        params, results = _params({"agent_id": agent_id})

        await ConversationManager._handle_transfer_to_agent(manager, params)

        assert results == [
            "Sorry, I couldn't find an agent called ''. Available agents: sales, ops"
        ]
        assert manager.current_persona_id == "sales"
