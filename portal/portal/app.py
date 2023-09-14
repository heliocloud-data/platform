"""
HelioCloud's Portal module UI & services.  Implements the main interface of the Portal
"""

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

from config import (
    region,
    aws_cognito_domain,
    user_pool_id,
    user_pool_client_id,
    user_pool_client_secret,
    redirect_url,
    site_url,
    flask_secret_key,
)
from ec2_config import image_id_dict
from messages import (
    keypair_message,
    access_key_message,
    make_session_token_message,
    download_message,
)

from aws import start_aws_session, get_weekly_overall_cost
from auth import get_user_info, set_token_cookie, get_tokens, get_cognito_public_keys
from ec2 import (
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
from access import (
    list_access_key,
    create_access_key,
    delete_access_key,
    update_key_status,
    get_session_token,
    list_mfa_devices,
    get_access_flag,
    get_aws_console_username,
)


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


@app.route("/", methods=["POST", "GET"])
def index():
    """
    Implements the main landing page of the Portal, where it will display:
    - The username of the user interacting w/ the portal
    - The running & stopped EC instances associated with that user
    - The costs associated with the user
    """
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        access_token = request.cookies.get("access_token_cookie")
        id_token = request.cookies.get("id_token_cookie")
        username, email = get_user_info(access_token)
        session["id_token"] = id_token
        session["username"] = username
        aws_session = start_aws_session(id_token)
        if request.method == "GET":
            instances = get_instances(aws_session, username)
            running_instances = [
                ins for ins in instances if ins["instance_state"] in ["running", "pending"]
            ]
            stopped_instances = [
                ins for ins in instances if ins["instance_state"] in ["stopped", "stopping"]
            ]
            # sort stopped and running by launch time and only show last 5 stopped instances
            if len(running_instances) > 0:
                running_instances = [
                    ins
                    for ins in sorted(
                        running_instances,
                        key=lambda item: item["LaunchTime"],
                        reverse=True,
                    )
                ]
            if len(stopped_instances) > 0:
                stopped_instances = [
                    ins
                    for ins in sorted(
                        stopped_instances,
                        key=lambda item: item["LaunchTime"],
                        reverse=True,
                    )
                ][:5]
            cost = get_weekly_overall_cost(aws_session, username)

            return render_template(
                "index.html",
                running_instances=running_instances,
                stopped_instances=stopped_instances,
                user=username,
                cost=cost,
            )
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/instance_action")
def instance_action():
    """
    Allows a Portal user to start, stop or terminate their AWS EC2 instances.
    """
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        id_token = session.get("id_token", None)
        aws_session = start_aws_session(id_token)
        instance_id = request.args.get("instance_id")
        if request.args.get("action") == "stop":
            try:
                stop_instance(aws_session, instance_id)
                return redirect(url_for("index"))
            except Exception as e:
                return render_template("error.html", error_code="Botocore Error", error_message=e)
        if request.args.get("action") == "start":
            try:
                start_instance(aws_session, instance_id)
                return redirect(url_for("index"))
            except Exception as e:
                return render_template("error.html", error_code="Botocore Error", error_message=e)
        if request.args.get("action") == "terminate":
            try:
                terminate_instance(aws_session, instance_id)
                return redirect(url_for("index"))
            except Exception as e:
                return render_template("error.html", error_code="Botocore Error", error_message=e)
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/launch_instance", methods=["POST", "GET"])
def launch_instance():
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        id_token = session.get("id_token", None)
        username = session.get("username", None)
        aws_session = start_aws_session(id_token)
        if request.method == "POST":
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
            try:
                running_instances = get_running_instances(aws_session, username)
                # max 3 instances running
                if len(running_instances) >= 3:
                    return render_template(
                        "error.html",
                        error_code="Too many running instances.",
                        error_message=f"You have {len(running_instances)} running instances. Please stop an instance before starting another.",
                    )
                else:
                    # check if all parameters selected
                    need_key = []
                    for key, val in instance_launch_info.items():
                        if val == None:
                            need_key.append(key)
                    if len(need_key) > 0:
                        return render_template(
                            "error.html",
                            error_code="Insufficient parameters",
                            error_message=f"Must choose values for parameters {need_key}.",
                        )
                    if (
                        instance_launch_info["volume_size"]
                        < instance_launch_info["min_volume_size"]
                    ):
                        return render_template(
                            "error.html",
                            error_code="Insufficient volume size",
                            error_message=f'The selected image requires at least {instance_launch_info["min_volume_size"]} GB of volume storage but you only opted for {instance_launch_info["volume_size"]} GB. Increase the volume size to use this image.',
                        )
                    else:
                        response = create_instance(aws_session, username, instance_launch_info)
                        if "Error" in response:
                            error = response["Error"]
                            return render_template(
                                "error.html",
                                error_code=error["Code"],
                                error_message=error["Message"],
                            )
                        else:
                            return redirect(url_for("index"))
            except Exception as e:
                return render_template("error.html", error_code="Botocore Error", error_message=e)
        else:
            # existing_images = get_custom_amis(aws_session, username)
            allowed_images_dict = {
                os: get_ami_info(aws_session, image_list)
                for os, image_list in image_id_dict[region].items()
            }
            existing_key_pairs = list_key_pairs(aws_session, username)
            key_pair_names = [kp["KeyName"] for kp in existing_key_pairs]
            instance_types = list_instance_types(aws_session)
            return render_template(
                "launch_instance.html",
                allowed_images=allowed_images_dict,
                key_pair_names=key_pair_names,
                instance_types=instance_types,
                user=username,
            )
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/access", methods=["POST", "GET"])
def get_access():
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        id_token = session.get("id_token", None)
        username = session.get("username", None)
        aws_session = start_aws_session(id_token)
        aws_console_username = get_aws_console_username(username)
        access_flag = get_access_flag(aws_session, aws_console_username)
        if access_flag:
            if request.method == "GET":
                active_access_keys, inactive_access_keys = list_access_key(
                    aws_session, aws_console_username
                )
                mfa_devices = list_mfa_devices(aws_session, aws_console_username)
                return render_template(
                    "access.html",
                    active_access_keys=active_access_keys,
                    inactive_access_keys=inactive_access_keys,
                    user=username,
                    mfa_devices=mfa_devices,
                    message="",
                    download=False,
                )
            else:
                if request.form.get("create_access_key") is not None:
                    try:
                        resp = create_access_key(aws_session, aws_console_username)
                        if "Error" in resp:
                            error = resp["Error"]
                            message = f'<p>Error: {error["Code"]} {error["Message"]}'
                        else:
                            access_key_id = resp["AccessKeyId"]
                            secret_access_key = resp["SecretAccessKey"]
                            active_access_keys, inactive_access_keys = list_access_key(
                                aws_session, aws_console_username
                            )
                            mfa_devices = list_mfa_devices(aws_session, aws_console_username)
                            session["download"] = secret_access_key
                            return render_template(
                                "access.html",
                                active_access_keys=active_access_keys,
                                inactive_access_keys=inactive_access_keys,
                                mfa_devices=mfa_devices,
                                user=username,
                                message=access_key_message.format(access_key_id, secret_access_key),
                                download="secret_key",
                            )
                    except Exception as e:
                        return render_template(
                            "error.html", error_code="Botocore Error", error_message=e
                        )
                if request.form.get("refresh_tokens") is not None:
                    try:
                        access_key_id = request.form.get("access_id")
                        secret_access_key = request.form.get("secret_key")
                        mfa_arn = request.form.get("mfa_arn")
                        mfa_code = request.form.get("mfa_code")
                        resp = get_session_token(
                            access_key_id, secret_access_key, mfa_arn, mfa_code
                        )
                        session_token_message = make_session_token_message(
                            resp["AccessKeyId"],
                            resp["SecretAccessKey"],
                            resp["SessionToken"],
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
                        return render_template(
                            "access.html",
                            active_access_keys=active_access_keys,
                            inactive_access_keys=inactive_access_keys,
                            mfa_devices=mfa_devices,
                            user=username,
                            message=session_token_message,
                            download="session_token",
                        )
                    except Exception as e:
                        return render_template(
                            "error.html", error_code="Botocore Error", error_message=e
                        )
        else:
            return render_template(
                "error.html",
                error_code="",
                error_message="Could not find an associated AWS account. Please contact an administrator to set up your AWS user account.",
            )
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/access_key_action")
def access_id_action():
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        id_token = session.get("id_token", None)
        aws_session = start_aws_session(id_token)
        username = session.get("username", None)
        access_key_id = request.args.get("access_key_id")
        aws_console_username = get_aws_console_username(username)
        if request.args.get("action") == "set_inactive":
            try:
                update_key_status(aws_session, aws_console_username, access_key_id, "Inactive")
                return redirect(url_for("get_access"))
            except Exception as e:
                return render_template("error.html", error_code="Botocore Error", error_message=e)
        if request.args.get("action") == "set_active":
            try:
                update_key_status(aws_session, aws_console_username, access_key_id, "Active")
                return redirect(url_for("get_access"))
            except Exception as e:
                return render_template("error.html", error_code="Botocore Error", error_message=e)
        if request.args.get("action") == "delete":
            try:
                delete_access_key(aws_session, aws_console_username, access_key_id)
                return redirect(url_for("get_access"))
            except Exception as e:
                return render_template("error.html", error_code="Botocore Error", error_message=e)
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/download")
def download():
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        type = request.args.get("type")
        username = session.get("username", None)
        message, filename = download_message(username, session, type)
        output = make_response(message)
        output.headers["Content-Disposition"] = f"attachment; filename={filename}"
        output.headers["Content-type"] = "text/plain"
        return output
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/keypairs", methods=["POST", "GET"])
def get_keypairs():
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        id_token = session.get("id_token", None)
        username = session.get("username", None)
        aws_session = start_aws_session(id_token)
        if request.method == "GET":
            keypairs = list_key_pairs(aws_session, username)
            return render_template(
                "keypairs.html",
                keypairs=keypairs,
                user=username,
                message="",
                download=False,
            )
        else:
            if request.form.get("create_keypair") is not None:
                keypair_name = request.form["keypair_name"]
                try:
                    resp = create_key_pair(aws_session, username, keypair_name)
                    if "Error" in resp:
                        error = resp["Error"]
                        message = f'<p>Error: {error["Code"]} {error["Message"]}'
                    else:
                        key_material = resp["KeyMaterial"]
                        keypairs = list_key_pairs(aws_session, username)
                        session["download"] = {
                            "name": keypair_name,
                            "material": key_material,
                        }
                        return render_template(
                            "keypairs.html",
                            keypairs=keypairs,
                            user=username,
                            message=keypair_message.format(keypair_name, keypair_name),
                            download=True,
                        )
                except Exception as e:
                    return render_template(
                        "error.html", error_code="Botocore Error", error_message=e
                    )

            elif request.form.get("delete_button") is not None:
                keypair_name = request.form.get("delete_button")
                try:
                    resp = delete_key_pair(aws_session, keypair_name)
                    if "Error" in resp:
                        error = resp["Error"]
                        message = f'<p>Error: {error["Code"]} {error["Message"]}'
                    else:
                        message = f"<p>Successfully deleted key pair {keypair_name}.</p>"
                    keypairs = list_key_pairs(aws_session, username)
                    return render_template(
                        "keypairs.html",
                        keypairs=keypairs,
                        user=username,
                        message=message,
                        download=False,
                    )
                except Exception as e:
                    return render_template(
                        "error.html", error_code="Botocore Error", error_message=e
                    )
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/quickstart", methods=["GET"])
def quickstart():
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        username = session.get("username", None)
        return render_template("quickstart.html", user=username)
    else:
        return redirect(aws_auth.get_sign_in_url())


@app.route("/login", methods=["GET", "POST"])
def login():
    return redirect(aws_auth.get_sign_in_url())


@app.route("/logout", methods=["GET", "POST"])
def logout():
    state = get_state(user_pool_id, user_pool_client_id)
    full_url = f"{aws_cognito_domain}/logout?response_type=code&client_id={user_pool_client_id}&state={state}&redirect_uri={site_url}/loggedin"
    return redirect(full_url)


@app.route("/loggedin", methods=["GET", "POST"])
def logged_in():
    access_token, id_token = get_tokens(request.args)
    resp = make_response(redirect(url_for("index")))
    set_token_cookie(resp, "access_token_cookie", access_token)
    set_token_cookie(resp, "id_token_cookie", id_token)
    return resp


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=80)
