import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import json

# Mock boto required environment variables so it can setup a dummy client
with patch("os.getenv") as mock_getenv:
    mock_getenv.side_effect = {
        "USER_POOL_ID": "mock-user-pool-id",
        "USER_POOL_CLIENT_SECRET": "mock-secret-key",
        "USER_POOL_CLIENT_ID": "mock-client-id",
        "REGION": "mock-region",
    }

    from registration_page.app import app


class RegistrationPageTests(unittest.TestCase):
    def setUp(self):
        """
        Set up the test client and common configurations.
        """
        self.client = app.test_client()
        self.client.testing = True
        self.headers = {"Content-Type": "application/json"}
        self.mock_cognito_client = patch("registration_page.app.cognito_client").start()

    def tearDown(self):
        """
        Stop all patches.
        """
        patch.stopall()

    def test_register_success(self):
        """
        Test successful registration.
        """
        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "affiliation": "example_affiliation",
        }
        self.mock_cognito_client.admin_create_user.return_value = {}
        self.mock_cognito_client.admin_disable_user.return_value = {}

        response = self.client.post("/register", data=json.dumps(payload), headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn("User registered successfully", response.json["message"])

    def test_register_failure(self):
        """
        Test registration failure due to Cognito exception.
        """
        payload = {
            "username": "test_user",
            "email": "test_user@example.com",
            "affiliation": "example_affiliation",
        }
        self.mock_cognito_client.admin_create_user.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "SomeErrorCode",
                    "Message": "Cognito error",
                }
            },
            operation_name="",
        )

        response = self.client.post("/register", data=json.dumps(payload), headers=self.headers)

        # Assert the response
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        """
        Test registration failure due to missing fields in the payload.
        """
        payload = {
            "username": "test_user",
            "email": "test_user@example.com"
            # Missing 'affiliation'
        }

        response = self.client.post("/register", data=json.dumps(payload), headers=self.headers)

        self.assertEqual(response.status_code, 400)

    def test_serve_index(self):
        """
        Test the root endpoint serving index.html.
        """
        with patch("registration_page.app.send_from_directory") as mock_send:
            mock_send.return_value = "index.html content"

            response = self.client.get("/")

            self.assertEqual(response.status_code, 200)
            mock_send.assert_called_with(app.static_folder, "index.html")

    def test_user_agreement(self):
        """
        Test the user agreement endpoint serving user_agreement.html.
        """
        with patch("registration_page.app.send_from_directory") as mock_send:
            mock_send.return_value = "user_agreement.html content"

            response = self.client.get("/user_agreement")

            self.assertEqual(response.status_code, 200)
            mock_send.assert_called_with(app.static_folder, "user_agreement.html")

    def test_health_check(self):
        """
        Test the health check endpoint.
        """
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "healthy"})
