"""
Messages used in various Portal interactions.
"""
keypair_message = "Created new key pair {}. Download then change permissions `chmod 400 {}.pem`."

access_key_message = r"<p>Your new access key was successfully created.</p><p><b>AWS Access Key ID</b>: {}</p><p><b>AWS Secret Access Key</b>: {}</p>"


def make_session_token_message(access_id, secret_key, session_token):
    session_token_message = f"<p>Your short-term session token was successfully generated. This is your new AWS session token:<br><code>{session_token}</code></p>"
    session_token_message += "<p>To update your environment variables:</p>"
    session_token_message += f"<p><code>export AWS_ACCESS_KEY_ID={access_id}<br>export AWS_SECRET_ACCESS_KEY={secret_key}<br>export AWS_SESSION_TOKEN={session_token}</code></p>"
    session_token_message += "<p>To update your AWS credentials file:</p>"
    session_token_message += f"<p><code>aws_access_key_id={access_id}<br>aws_secret_access_key={secret_key}<br>aws_session_token={session_token}</code></p>"
    return session_token_message


def make_session_token_download(access_id, secret_key, session_token):
    download_message = f"export AWS_ACCESS_KEY_ID={access_id}\nexport AWS_SECRET_ACCESS_KEY={secret_key}\nexport AWS_SESSION_TOKEN={session_token}"
    return download_message


def download_message(username, session, type):
    print(session)
    if type == "keypair":
        keypair = session.get("download")
        keypair_name = keypair["name"]
        key_material = keypair["material"]
        content = key_material
        filename = f"{keypair_name}.pem"
        session.pop("download", None)
    elif type == "secret_key":
        secret_key = session.get("download")
        content = secret_key
        filename = f"{username}_secret_access_key.txt"
    elif type == "session_token":
        tokens = session.get("download")
        content = make_session_token_download(tokens["access"], tokens["secret"], tokens["token"])
        filename = f"{username}_session_token.txt"
    else:
        content = None
        filename = ""
    session.pop("download", None)
    return content, filename
