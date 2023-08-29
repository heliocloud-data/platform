from flask_jwt_extended.config import config as jwt_config
import requests
from base64 import b64encode
from config import (
    aws_cognito_domain,
    redirect_url,
    user_pool_client_id,
    user_pool_client_secret,
    user_pool_id,
    region,
)
import json


def get_cognito_public_keys():
    url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    resp = requests.get(url)
    return json.dumps(json.loads(resp.text)["keys"][1])


def get_tokens(request_args):
    """Get access and ID tokens."""
    code = request_args.get("code")
    token_url = f"{aws_cognito_domain}/oauth2/token"
    data = {
        "code": code,
        "redirect_uri": redirect_url,
        "client_id": user_pool_client_id,
        "grant_type": "authorization_code",
    }
    secret = b64encode(f"{user_pool_client_id}:{user_pool_client_secret}".encode("utf-8")).decode(
        "utf-8"
    )
    headers = {"Authorization": f"Basic {secret}"}
    response = requests.post(token_url, data=data, headers=headers)
    response_json = response.json()
    access_token = response_json["access_token"]
    id_token = response_json["id_token"]
    return access_token, id_token


def set_token_cookie(resp, token_name, token_value, max_age=30 * 60):
    resp.set_cookie(
        token_name,
        value=token_value,
        max_age=max_age,
        # secure=jwt_config.cookie_secure,
        # httponly=True,
        # domain=jwt_config.cookie_domain,
        # path=jwt_config.access_cookie_path,
        # samesite=jwt_config.cookie_samesite,
    )
    return resp


def get_user_info(access_token):
    user_url = f"{aws_cognito_domain}/oauth2/userInfo"
    header = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(user_url, headers=header)
    response_json = response.json()
    username = response_json["username"]
    email = response_json["email"]
    return username, email
