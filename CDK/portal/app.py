"""
HelioCloud's Portal module UI & services.  Implements the main interface of the Portal
"""
from typing import Any

import boto3
from botocore.exceptions import ClientError
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    make_response,
    session,
)
from flask_awscognito import AWSCognitoAuthentication
from flask_awscognito.utils import get_state
from jwt.algorithms import RSAAlgorithm
from flask_jwt_extended import (
    JWTManager,
    verify_jwt_in_request,
    get_jwt_identity,
)
from flask_cors import CORS
from waitress import serve

# Local imports
from lib.config import (
    region,
    aws_cognito_domain,
    user_pool_id,
    user_pool_client_id,
    user_pool_client_secret,
    redirect_url,
    site_url,
    flask_secret_key,
)
from lib.ec2_config import image_id_dict
from lib.messages import (
    KEYPAIR_MESSAGE,
    ACCESS_KEY_MESSAGE,
    make_session_token_message,
    download_message,
)

from lib.aws import start_aws_session, get_weekly_overall_cost
from lib.auth import get_user_info, set_token_cookie, get_tokens, get_cognito_public_keys
from lib.ec2 import (
    get_instances,
    create_instance,
    list_instance_types,
    list_key_pairs,
    stop_instance,
    terminate_instance,
    start_instance,
    create_key_pair,
    delete_key_pair,
    get_ami_info,
    get_running_instances,
)
from lib.access import (
    list_access_key,
    create_access_key,
    delete_access_key,
    update_key_status,
    get_session_token,
    list_mfa_devices,
    get_access_flag,
    get_aws_console_username,
)

# Users are capped to a maximum of 3 running EC2 instances
MAX_INSTANCES = 3

# Create a new app
app = Flask(__name__)

# cognito setup TAKE OUT
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_ALGORITHM"] = "RS256"
app.config["JWT_IDENTITY_CLAIM"] = "sub"
app.config["AWS_DEFAULT_REGION"] = region
app.config["AWS_COGNITO_DOMAIN"] = aws_cognito_domain
app.config["AWS_COGNITO_USER_POOL_ID"] = user_pool_id
app.config["AWS_COGNITO_USER_POOL_CLIENT_ID"] = user_pool_client_id
app.config["AWS_COGNITO_USER_POOL_CLIENT_SECRET"] = user_pool_client_secret
app.config["AWS_COGNITO_REDIRECT_URL"] = redirect_url
app.config["JWT_PUBLIC_KEY"] = RSAAlgorithm.from_jwk(get_cognito_public_keys())
app.config["SECRET_KEY"] = flask_secret_key

CORS(app)
aws_auth = AWSCognitoAuthentication(app)
jwt = JWTManager(app)


# Private methods for addressing certain renderings
def __render_error(code: str, message: str):
    """
    Renders an error via error.html
    """
    return render_template("error.html", error_code=code, error_message=message)


def __render_client_error(error: ClientError):
    """
    Renders the error template with the message.  Defaults to an error code of
    botocore error since thats what most (all?) errors will be
    """
    return __render_error(code="Botocore Error", message=str(error))


def __render_launch_page(aws_session, username: str) -> str:
    """
    Shows the launch page for instances
    """
    # existing_images = get_custom_amis(aws_session, username)
    allowed_images_dict = {
        os: get_ami_info(aws_session, image_list)
        for os, image_list in image_id_dict[region].items()
    }
    return render_template(
        "launch_instance.html",
        allowed_images=allowed_images_dict,
        key_pair_names=[kp["KeyName"] for kp in list_key_pairs(aws_session, username)],
        instance_types=list_instance_types(aws_session),
        user=username,
    )


# pylint: disable=too-many-arguments
def __render_access_page(
    active_keys: list[str],
    inactive_keys: list[str],
    username: str,
    mfa_devices: list[str],
    download_msg: str,
    message="",
) -> str:
    """
    Shows the access page
    """
    return render_template(
        "access.html",
        active_access_keys=active_keys,
        inactive_access_keys=inactive_keys,
        mfa_devices=mfa_devices,
        user=username,
        message=message,
        download=download_msg,
    )


# pylint: enable=too-many-arguments


def __render_keypairs(key_pairs: Any, user: str, message: str, download_flag: bool) -> str:
    """
    Render key pairs page
    """
    return render_template(
        "keypairs.html",
        keypairs=key_pairs,
        user=user,
        message=message,
        download=download_flag,
    )


# Private methods for simplifying business logic in the routes
def __create_access_key(aws_session, aws_console_username: str, username: str):
    """
    Private method for creating an access key
    """
    try:
        # Create a new access key for the user
        resp = create_access_key(aws_session, aws_console_username)
        if "Error" in resp:
            error = resp["Error"]
            active_access_keys = None
            inactive_access_keys = None
            mfa_devices = None
            message = f'<p>Error: {error["Code"]} {error["Message"]}'
        else:
            access_key_id = resp["AccessKeyId"]
            secret_access_key = resp["SecretAccessKey"]
            active_access_keys, inactive_access_keys = list_access_key(
                aws_session, aws_console_username
            )
            mfa_devices = list_mfa_devices(aws_session, aws_console_username)
            session["download"] = secret_access_key
            message = ACCESS_KEY_MESSAGE.format(access_key_id, secret_access_key)

        # Render a response indicating successful key creation & download permitted, or that
        # an error occurred
        return __render_access_page(
            active_keys=active_access_keys,
            inactive_keys=inactive_access_keys,
            mfa_devices=mfa_devices,
            username=username,
            message=message,
            download_msg="secret_key",
        )

    # Likely a boto3 exception happened
    except ClientError as err:
        return __render_client_error(error=err)


def __refresh_tokens(aws_session, aws_console_username: str, username: str):
    """
    Refreshing tokens
    """
    try:
        access_key_id = request.form.get("access_id")
        secret_access_key = request.form.get("secret_key")
        mfa_arn = request.form.get("mfa_arn")
        mfa_code = request.form.get("mfa_code")

        # Fetch a session token for this user in the Portal's region
        user_session = boto3.Session(
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        resp = get_session_token(user_session, mfa_arn, mfa_code)

        # Display the session token
        session_token_message = make_session_token_message(
            resp["AccessKeyId"], resp["SecretAccessKey"], resp["SessionToken"]
        )

        active_access_keys, inactive_access_keys = list_access_key(
            aws_session, aws_console_username
        )
        mfa_devices = list_mfa_devices(aws_session, aws_console_username)
        session["download"] = {
            "access": resp["AccessKeyId"],
            "secret": resp["SecretAccessKey"],
            "token": resp["SessionToken"],
        }

        # Display the download option for pulling the session token
        return __render_access_page(
            active_keys=active_access_keys,
            inactive_keys=inactive_access_keys,
            mfa_devices=mfa_devices,
            username=username,
            message=session_token_message,
            download_msg="session_token",
        )

        # Boto 3 exception happened
    except ClientError as error:
        return __render_client_error(error)


def __validate_launch_instance(aws_session, username: str, launch_info: dict) -> (bool, str, str):
    """
    Validate the launch information provided to determine if launching another EC2 instance
    should be allowed.
    Returns:
        True if the launch should be allowed
        False if the launch should not be allowed. The following 2 strings contain an error
        code and message to use in rendering an error response.
    """
    # First, check that the user does not have more than MAX_INSTANCES running
    try:
        # First, check that the user does not have more than MAX_INSTANCES running
        running_instances = get_running_instances(aws_session, username)
        if len(running_instances) >= MAX_INSTANCES:
            return (
                False,
                "Too many running instances.",
                f"You have {len(running_instances)}. "
                f"Please stop an instance before "
                f"starting more.",
            )

        # Check that the launch info is fully populated
        keys_missing_vals = [val for key, val in launch_info.items() if val is None]
        if len(keys_missing_vals) > 0:
            return (
                False,
                "Insufficient parameters.",
                f"Must choose values " f"for parameters {keys_missing_vals}.",
            )

        # Check the volume size
        if launch_info["volume_size"] < launch_info["min_volume_size"]:
            return (
                False,
                "Insufficient volume size",
                f"The selected image requires at least "
                f"{launch_info['min_volume_size']} GB of "
                f"volume storage but you only opted for "
                f"{launch_info['volume_size']} GB. "
                f"Increase the volume size to use this image.",
            )
        # Valid
        return True, "", ""

    except ClientError as err:
        return False, "Botocore error", str(err)


# Start of routes & their controllers
@app.route("/", methods=["POST", "GET"])
def index():
    """
    Implements the main landing page of the Portal, where it will display:
    - The username of the user interacting w/ the portal
    - The running & stopped EC instances associated with that user
    - The costs associated with the user
    """
    verify_jwt_in_request(optional=True)

    # Check for JWT
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # Get session information
    access_token = request.cookies.get("access_token_cookie")
    id_token = request.cookies.get("id_token_cookie")
    username = get_user_info(access_token)[0]  # only need username
    session["id_token"] = id_token
    session["username"] = username
    aws_session = start_aws_session(id_token)

    # Going to get the lists of instances associated with a user and their costs
    # to display.
    if request.method == "GET":
        # Get all the AWS EC2 instances associated with the user
        instances = get_instances(aws_session, username)
        running_instances = [
            ins for ins in instances if ins["instance_state"] in ["running", "pending"]
        ]
        stopped_instances = [
            ins for ins in instances if ins["instance_state"] in ["stopped", "stopping"]
        ]

        # Sort running instances by start time for display purposes
        if len(running_instances) > 0:
            running_instances = list(
                sorted(running_instances, key=lambda item: item["LaunchTime"], reverse=True)
            )

        # Show only the last 5 stopped instances
        if len(stopped_instances) > 0:
            stopped_instances = list(
                sorted(stopped_instances, key=lambda item: item["LaunchTime"], reverse=True)
            )[:5]

        # Fetch weekly costs
        cost = get_weekly_overall_cost(aws_session, username)

        # Show running & stopped instances for the user w/ associated costs
        return render_template(
            "index.html",
            running_instances=running_instances,
            stopped_instances=stopped_instances,
            user=username,
            cost=cost,
        )

    # Unexpected request method
    return redirect(aws_auth.get_sign_in_url())


@app.route("/instance_action")
def instance_action():
    """
    Allows a Portal user to start, stop or terminate their AWS EC2 instances.
    """
    verify_jwt_in_request(optional=True)

    # Check for JWT
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # One of start, stop or terminate was requested
    action = request.args.get("action", None)
    if action in ["start", "stop", "terminate"]:
        id_token = session.get("id_token", None)
        aws_session = start_aws_session(id_token)
        instance_id = request.args.get("instance_id")

        try:
            if action == "stop":
                stop_instance(aws_session, instance_id)
            if action == "start":
                start_instance(aws_session, instance_id)
            if action == "terminate":
                terminate_instance(aws_session, instance_id)

        # Boto exception
        except ClientError as err:
            return __render_client_error(err)

        # Successful operation
        return redirect(url_for("index"))

    # Unrecognized action. Send requester back to signin.
    return redirect(aws_auth.get_sign_in_url())


@app.get("/launch_instance")
def show_launched_ec2_instances():
    """
    Show the launched instances.
    """

    # Instead, we will show the user the launch page
    verify_jwt_in_request(optional=True)

    # If no JWT found, redirect to signin
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # Show the launch page
    id_token = session.get("id_token", None)
    username = session.get("username", None)
    aws_session = start_aws_session(id_token)
    return __render_launch_page(aws_session, username)


@app.post("/launch_instance")
def launch_ec2_instance():
    """
    Route for launching AWS EC2 instances
    """
    verify_jwt_in_request(optional=True)

    # If no JWT found, redirect to signin
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # otherwise do everything else
    id_token = session.get("id_token", None)
    username = session.get("username", None)
    aws_session = start_aws_session(id_token)

    # Launching an EC2 instance
    image_output = request.form.get("image_output").split(",")
    instance_launch_info = {
        "instance_name": request.form.get("instance_name_for_custom"),
        "key_pair": request.form.get("key_pair"),
        "instance_type": request.form.get("instance_type"),
        "image_id": image_output[0],
        "volume_size": int(request.form.get("volume_size")),
        "device_name": image_output[1],
        "volume_type": image_output[2],
        "min_volume_size": int(image_output[3]),
    }

    # If not valid, return an error page rendering
    valid, msg_1, msg_2 = __validate_launch_instance(aws_session, username, instance_launch_info)
    if not valid:
        return __render_error(msg_1, msg_2)

    # Otherwise, create an instance
    try:
        response = create_instance(aws_session, username, instance_launch_info)

        # Error when trying to create it
        if "Error" in response:
            return __render_error(
                code=response["Error"]["Code"], message=response["Error"]["Message"]
            )

        # Instance created successfully.
        return redirect(url_for("index"))

    # Something went wrong in communications with boto
    except ClientError as err:
        return __render_client_error(error=err)


@app.get("/access")
def display_access():
    """
    Display the access information associated with the user
    """
    verify_jwt_in_request(optional=True)

    # Check for JWT
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # Got the JWI identity
    username = session.get("username", None)
    aws_session = start_aws_session(session.get("id_token", None))
    aws_console_username = get_aws_console_username(username)

    # Couldn't find an AWS account for this user.
    if not get_access_flag(aws_session, aws_console_username):
        return __render_error(
            code="",
            message="Could not find an associated AWS account. "
            "Please contact an administrator to set up your AWS user account.",
        )

    # Display the access information associated with the user:
    # keys, username & mfa devices
    active_access_keys, inactive_access_keys = list_access_key(aws_session, aws_console_username)
    mfa_devices = list_mfa_devices(aws_session, aws_console_username)
    return __render_access_page(
        active_keys=active_access_keys,
        inactive_keys=inactive_access_keys,
        username=username,
        mfa_devices=mfa_devices,
        message="",
        download_msg=str(False),
    )


@app.post("/access")
def access():
    """
    Route for access operations:  viewing
    """
    verify_jwt_in_request(optional=True)

    # Check for JWT
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # Got the JWI identity
    username = session.get("username", None)
    aws_session = start_aws_session(session.get("id_token", None))
    aws_console_username = get_aws_console_username(username)
    access_flag = get_access_flag(aws_session, aws_console_username)

    # Couldn't find an AWS account for this user.
    if not access_flag:
        return __render_error(
            code="",
            message="Could not find an associated AWS account. "
            "Please contact an administrator to set up your AWS user account.",
        )

    # Create an AWS Access Key for the user
    if request.form.get("create_access_key") is not None:
        return __create_access_key(
            aws_session=aws_session, aws_console_username=aws_console_username, username=username
        )

    # Refreshing user AWS tokens
    if request.form.get("refresh_tokens") is not None:
        return __refresh_tokens(
            aws_session=aws_session, aws_console_username=aws_console_username, username=username
        )

    # Unexpected request type or parameters. Return to signin
    return redirect(aws_auth.get_sign_in_url())


@app.route("/access_key_action")
def access_key_action():
    """
    Route for taking action on an access key id. Possible actions are:
        - setting the key inactive
        - setting the key active
        - deleting the key
    """
    verify_jwt_in_request(optional=True)

    # No JWT found, redirect user to signin
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # One of setting active, inactive or deleting for a key was requested
    action = request.args.get("action")
    if action in ["set_active", "set_inactive", "delete"]:
        # Extract details from the session that will be needed for access key id operations
        id_token = session.get("id_token", None)
        aws_session = start_aws_session(id_token)
        username = session.get("username", None)
        access_key_id = request.args.get("access_key_id")
        aws_console_username = get_aws_console_username(username)

        try:
            if action == "set_active":
                update_key_status(aws_session, aws_console_username, access_key_id, "Active")
            if action == "set_inactive":
                update_key_status(aws_session, aws_console_username, access_key_id, "Inactive")
            if action == "delete":
                delete_access_key(aws_session, aws_console_username, access_key_id)
        except ClientError as err:
            return __render_client_error(error=err)

        return redirect(url_for("get_access"))

    # Not sure what the request was, so go back to signin
    return redirect(aws_auth.get_sign_in_url())


@app.route("/download")
def download():
    """
    Route for supporting downloads
    """
    verify_jwt_in_request(optional=True)
    # Check that JWt information is present
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # Determine the type of download and construct the appropriate response
    download_type = request.args.get("type")
    username = session.get("username", None)
    message, filename = download_message(username, session, download_type)
    output = make_response(message)
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/plain"
    return output


@app.get("/keypairs")
def get_keypairs():
    """
    Get and render keypairs
    """
    verify_jwt_in_request(optional=True)

    # If no JWT information, return to signin
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # Get session information for request
    username = session.get("username", None)
    aws_session = start_aws_session(session.get("id_token", None))

    # Get and display the key pairs for the user
    key_pairs = list_key_pairs(aws_session, username)
    return __render_keypairs(key_pairs=key_pairs, user=username, message="", download_flag=False)


@app.post("/keypairs")
def keypairs():
    """
    Route for working with AWS EC2 key pairs - retrieving, creating & deleting
    """
    verify_jwt_in_request(optional=True)

    # If no JWT information, return to signin
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    # Get session information for request
    username = session.get("username", None)
    aws_session = start_aws_session(session.get("id_token", None))

    # Check if we should be creating a keypair instead
    if request.form.get("create_keypair") is not None:
        keypair_name = request.form["keypair_name"]
        try:
            # Attempt to create the keypair
            resp = create_key_pair(aws_session, username, keypair_name)

            # Ran into an error
            if "Error" in resp:
                error = resp["Error"]
                message = f'<p>Error: {error["Code"]} {error["Message"]}'

            # Successful key creation
            else:
                key_material = resp["KeyMaterial"]
                session["download"] = {
                    "name": keypair_name,
                    "material": key_material,
                }
                message = KEYPAIR_MESSAGE.format(keypair_name, keypair_name)

            # Render a response showing all the key pairs, then a message indicating
            # either that a new key pair was created or an error occurred
            key_pairs = list_key_pairs(aws_session, username)
            return __render_keypairs(
                key_pairs=key_pairs, user=username, message=message, download_flag=True
            )

        # Boto problem, so render an error
        except ClientError as error:
            return __render_client_error(error)

    # Deleting a key pair
    if request.form.get("delete_button") is not None:
        keypair_name = request.form.get("delete_button")
        try:
            resp = delete_key_pair(aws_session, keypair_name)
            if "Error" in resp:
                error = resp["Error"]
                message = f'<p>Error: {error["Code"]} {error["Message"]}'
            else:
                message = f"<p>Successfully deleted key pair {keypair_name}.</p>"

            # Render a response with the remaining key pairs and
            # a message indicating the keypair was deleted (or there was an error).
            key_pairs = list_key_pairs(aws_session, username)
            return __render_keypairs(
                key_pairs=key_pairs, user=username, message=message, download_flag=False
            )

        # Boto 3 problem
        except ClientError as error:
            return __render_client_error(error)

    # Unexpected request type & parameters.  Send the user back to the signin.
    return redirect(aws_auth.get_sign_in_url())


@app.route("/quickstart", methods=["GET"])
def quickstart():
    """
    Quickstart workflow.
    """
    verify_jwt_in_request(optional=True)

    # Check for JWT
    if get_jwt_identity() is None:
        return redirect(aws_auth.get_sign_in_url())

    username = session.get("username", None)
    return render_template("quickstart.html", user=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login route. Redirects user to the sign-in workflow.
    """
    return redirect(aws_auth.get_sign_in_url())


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Logout route.  Redirects user to the Cognito logout URL.
    """
    state = get_state(user_pool_id, user_pool_client_id)
    full_url = (
        f"{aws_cognito_domain}/logout?"
        f"response_type=code&client_id={user_pool_client_id}&"
        f"state={state}&redirect_uri={site_url}/loggedin"
    )
    return redirect(full_url)


@app.route("/loggedin", methods=["GET", "POST"])
def logged_in():
    """
    Sets access & id token cookies on the requesting client,
    indicating they are logged in.
    """

    access_token, id_token = get_tokens(request.args)
    resp = make_response(redirect(url_for("index")))
    set_token_cookie(resp, "access_token_cookie", access_token)
    set_token_cookie(resp, "id_token_cookie", id_token)
    return resp


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=80)
