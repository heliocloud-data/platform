"""
Messages used in various Portal interactions.
"""
KEYPAIR_MESSAGE = "Created new key pair {}. Download then change permissions `chmod 400 {}.pem`."
ACCESS_KEY_MESSAGE = (
    r"<p>Your new access key was successfully created.</p>"
    r"<p><b>AWS Access Key ID</b>: {}</p><p><b>AWS Secret Access Key</b>: {}</p>"
)


def make_session_token_message(access_id, secret_key, session_token):
    """
    Returns formatted HTML informing the viewer regarding the creation of an
    AWS Session Token and instructions on its proper usage.
    """
    message = (
        f"<p>"
        f"Your short-term session token was successfully generated. "
        f"This is your new AWS session token:"
        f"<br><code>{session_token}</code>"
        f"</p>"
    )
    message += "<p>To update your environment variables:</p>"
    message += (
        f"<p>"
        f"<code>export AWS_ACCESS_KEY_ID={access_id}"
        f"<br>export AWS_SECRET_ACCESS_KEY={secret_key}"
        f"<br>export AWS_SESSION_TOKEN={session_token}</code>"
        f"</p>"
    )
    message += "<p>To update your AWS credentials file:</p>"
    message += (
        f"<p>"
        f"<code>aws_access_key_id={access_id}"
        f"<br>aws_secret_access_key={secret_key}"
        f"<br>aws_session_token={session_token}</code>"
        f"</p>"
    )
    return message


def make_session_token_download(access_id, secret_key, session_token):
    """
    Download message for an AWS Session Token.
    """
    message = (
        f"export AWS_ACCESS_KEY_ID={access_id}\n"
        f"export AWS_SECRET_ACCESS_KEY={secret_key}\n"
        f"export AWS_SESSION_TOKEN={session_token}"
    )
    return message


def download_message(username, session, download_type: str):
    """
    General download message that varies based on the type of download.
    download_type may be one of:
    - keypair
    - secret_key
    - session_token
    """
    if download_type == "keypair":
        keypair = session.get("download")
        keypair_name = keypair["name"]
        key_material = keypair["material"]
        content = key_material
        filename = f"{keypair_name}.pem"
        session.pop("download", None)
    elif download_type == "secret_key":
        secret_key = session.get("download")
        content = secret_key
        filename = f"{username}_secret_access_key.txt"
    elif download_type == "session_token":
        tokens = session.get("download")
        content = make_session_token_download(tokens["access"], tokens["secret"], tokens["token"])
        filename = f"{username}_session_token.txt"
    else:
        content = None
        filename = ""
    session.pop("download", None)
    return content, filename
