"""
Tests for ec2.py in the Portal
"""
import portal.lib.messages as messages


def test_make_session_token_message():
    result = messages.make_session_token_message(
        access_id="1", session_token="ABC", secret_key="123"
    )

    # Check for some expected content
    assert "export AWS_ACCESS_KEY_ID=1" in result
    assert "export AWS_SECRET_ACCESS_KEY=123" in result
    assert "export AWS_SESSION_TOKEN=ABC" in result


def test_make_session_token_download():
    result = messages.make_session_token_download(
        access_id="1", session_token="ABC", secret_key="123"
    )

    # Check for some expected content
    assert "export AWS_ACCESS_KEY_ID=1" in result
    assert "export AWS_SECRET_ACCESS_KEY=123" in result
    assert "export AWS_SESSION_TOKEN=ABC" in result


def test_download_message_keypair():
    # TODO: To be implemented - difficult due to embedded calls to the flask session
    # in messages.download_message that create a popup
    pass
