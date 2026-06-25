"""
Contains various functions for interacting with heliocloud
configurations.
"""

import json
import os
import subprocess

HELIOCLOUD_TERRAFORM_BINARY_ENV_VAR="HELIOCLOUD_TERRAFORM_BINARY"
HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER_ENV_VAR='HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER'
HELIOCLOUD_TERRAFORM_ENVIRONMENT_ENV_VAR='HELIOCLOUD_TERRAFORM_ENVIRONMENT'

DEFAULT_HELIOCLOUD_TERRAFORM_BINARY="tofu"
# pylint: disable=line-too-long


CONTEXT_CACHE = {

}

def create_heliocloud_context_file(context_name, context):
    filename = f".heliocloud-context-{context_name}.json"

    with open(filename, "w", encoding="utf-8") as write_file:
        json.dump(context, write_file, indent=4)

def load_heliocloud_context_from_terraform_outputs(env=None, environment_folder=None):
    if env is None or len(env) == 0:
        env = os.environ.get(HELIOCLOUD_TERRAFORM_ENVIRONMENT_ENV_VAR, None)
    if env is None:
        env = "dev"

    if environment_folder is None or len(environment_folder) == 0:
        environment_folder = os.environ.get(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER_ENV_VAR, None)
    if environment_folder is None:
        environment_folder = "./"

    cmd_args = [
        os.environ.get(HELIOCLOUD_TERRAFORM_BINARY_ENV_VAR, DEFAULT_HELIOCLOUD_TERRAFORM_BINARY),
        "output",
        f"-var-file={environment_folder}/environments/{env}/terraform.tfvars.json",
        "-json",
        "-show-sensitive"
    ]

    try:
        result = subprocess.run(cmd_args, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to generate heliocloud-context from working terraform/tofu context.  App returned exit code {e.returncode}.  Command Args: {cmd_args}")

    return json.loads(result.stdout)

def load_heliocloud_context(context_name=None):
    if context_name is None or len(context_name) == 0:
        # Context is unset, generate one
        context_name = 'auto'

    if context_name in CONTEXT_CACHE:
        return CONTEXT_CACHE[context_name]
    
    if context_name == 'auto':
        create_heliocloud_context_file(context_name, load_heliocloud_context_from_terraform_outputs())

    filename = f".heliocloud-context-{context_name}.json"
    print(f"Loading heliocloud context file {filename}")
    with open(filename, "r", encoding="utf-8") as read_file:
        context = json.load(read_file)
    CONTEXT_CACHE[context_name] = context
    return context

def get_base_url(hc_instance, app):
    """
    Get the base URL for a given application
    """
    if app == "portal":
        return get_portal_url(hc_instance)
    if app == "daskhub":
        return get_daskhub_url(hc_instance)
    raise ValueError(f"Unrecognized app {app}")


def get_portal_url(context_name):
    """
    Get the base URL of portal.
    """
    ctx = load_heliocloud_context(context_name)

    return f"https://{ctx['portal_fqdn']['value']}"


def get_daskhub_url(context_name):
    """
    Get the base URL of daskhub.
    """
    ctx = load_heliocloud_context(context_name)

    return f"https://{ctx['daskhub_fqdn']['value']}"

def get_user_pool_id_by_heliocloud_name(context_name):
    ctx = load_heliocloud_context(context_name)

    return ctx['cognito_user_pool_id']['value']
