"""
Tests for ec2.py in the Portal
"""
import unittest
import portal.lib.messages as messages


class TestMessages(unittest.TestCase):
    def test_make_session_token_message(self):
        result = messages.make_session_token_message(
            access_id="1", session_token="ABC", secret_key="123"
        )

        # Check for some expected content
        self.assertIn("export AWS_ACCESS_KEY_ID=1", result)
        self.assertIn("export AWS_SECRET_ACCESS_KEY=123", result)
        self.assertIn("export AWS_SESSION_TOKEN=ABC", result)

    def test_make_session_token_download(self):
        result = messages.make_session_token_download(
            access_id="1", session_token="ABC", secret_key="123"
        )

        # Check for some expected content
        self.assertIn("export AWS_ACCESS_KEY_ID=1", result)
        self.assertIn("export AWS_SECRET_ACCESS_KEY=123", result)
        self.assertIn("export AWS_SESSION_TOKEN=ABC", result)

    def test_download_message_keypair(self):
        # TODO: To be implemented - difficult due to embedded calls to the flask session
        # in messages.download_message that create a popup
        pass
