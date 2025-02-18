"""
Registration Page web application responsible for serving registraiton front end and
cognito interface backend.
"""

import os
from flask import Flask, send_from_directory, jsonify, request
import boto3
from botocore.exceptions import ClientError


class Config:
    """
    Configuration variables for AWS authentication.
    """

    COGNITO_USER_POOL_ID = os.getenv("USER_POOL_ID")
    COGNITO_SECRET_KEY = os.getenv("USER_POOL_CLIENT_SECRET")
    COGNITO_CLIENT_ID = os.getenv("USER_POOL_CLIENT_ID")
    AWS_REGION = os.getenv("REGION")


cognito_client = boto3.client("cognito-idp", region_name=Config.AWS_REGION)

app = Flask(__name__, static_folder="static")


@app.route("/register", methods=["POST"])
def register():
    """
    Registration endpoint - creates a user and disables them. Full user access requires
    manual intervention.
    """
    try:
        username = request.json["username"]
        email = request.json["email"]
        affiliation = request.json["affiliation"]
        password = request.json["password"]

        cognito_client.admin_create_user(
            UserPoolId=Config.COGNITO_USER_POOL_ID,
            Username=username,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:affiliation", "Value": affiliation},
            ],
            MessageAction="SUPPRESS",
            TemporaryPassword=password,
        )

        cognito_client.admin_disable_user(UserPoolId=Config.COGNITO_USER_POOL_ID, Username=username)

        return (
            jsonify({"message": "User registered successfully."}),
            200,
        )
    except (ClientError, KeyError) as error:
        return jsonify({"error": str(error)}), 400


@app.route("/")
def serve_index():
    """
    Default endpoint.
    """
    return send_from_directory(app.static_folder, "index.html")


@app.route("/user_agreement")
def user_agreement():
    """
    User agreement endpoint.
    """
    return send_from_directory(app.static_folder, "user_agreement.html")


@app.route("/health")
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}, 200
