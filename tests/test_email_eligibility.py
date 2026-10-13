import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test")

from gtm_agent.gtm_agent import SYSTEM_PROMPT, send_prospect_email


class SendProspectEmailTests(unittest.TestCase):
    def setUp(self):
        self.runtime = SimpleNamespace(config={"metadata": {"user_id": "REP-10001"}})
        self.from_rep = {"email": "rep@example.com", "name": "Test Rep"}

    def test_disqualified_source_record_blocks_send(self):
        prospect = {
            "prospect_id": "LEAD-50001",
            "name": "Priya Nair",
            "email": "priya.nair@brightwaveapps.com",
            "disqualified": False,
        }

        with patch("gtm_agent.gtm_agent.uuid.uuid4") as generate_id:
            result = send_prospect_email.func(
                prospect, "Hello", "Message", self.runtime, self.from_rep
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["error"], "Prospect LEAD-50001 is disqualified; email not sent."
        )
        generate_id.assert_not_called()

    def test_missing_source_record_blocks_before_message_id_generation(self):
        prospect = {"prospect_id": "LEAD-MISSING", "email": "prospect@example.com"}

        with (
            patch("gtm_agent.gtm_agent.data_service.get_prospect_record", return_value=None),
            patch("gtm_agent.gtm_agent.uuid.uuid4") as generate_id,
        ):
            result = send_prospect_email.func(
                prospect, "Hello", "Message", self.runtime, self.from_rep
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"], "Prospect LEAD-MISSING not found; email not sent.")
        generate_id.assert_not_called()

    def test_eligible_prospect_can_be_sent_email(self):
        prospect = {
            "prospect_id": "LEAD-90003",
            "name": "Grace Adeyemi",
            "email": "grace.adeyemi@fairviewlabs.com",
        }

        with patch(
            "gtm_agent.gtm_agent.uuid.uuid4",
            return_value=SimpleNamespace(hex="1234567890abcdef"),
        ):
            result = send_prospect_email.func(
                prospect, "Hello", "Message", self.runtime, self.from_rep
            )

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["message_id"], "msg-1234567890ab")
        self.assertEqual(result["to"], prospect["email"])

    def test_prompt_explains_blocked_sends_without_claiming_success(self):
        self.assertIn("clearly explain when and why to the rep", SYSTEM_PROMPT)
        self.assertIn("do not claim the email was sent", SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
