"""
Utils for working with Jinja templates.
"""

import argparse
import base64
import glob
from pathlib import Path

import jinja2
import json
import os
import secrets
import shutil
import subprocess
import yaml

SECRET_HEX_IN_BYTES = 32

def apply_jinja_templates_by_dir(
    template_src_folder: str, template_dest_folder: str, render_params: dict
):
    """
    Go through the jinja templates in the source folder, fill out the template
    and put the resulting populated files in the destination folder.
    """
    env = jinja2.Environment()

    for file in glob.glob(f"{template_src_folder}/**", recursive=True):
        if os.path.isdir(file):
            continue

        file_relative_to_src_folder = file[len(template_src_folder) + 1 :]
        dest_file = f"{template_dest_folder}/{file_relative_to_src_folder}"
        os.makedirs(Path(dest_file).parent, exist_ok=True)

        if file.endswith(".j2"):
            dest_relative_file_name = env.from_string(os.path.splitext(file_relative_to_src_folder)[0]).render(render_params)

            subpath = ""
            # Kustomize units 
            if dest_relative_file_name == "kustomization.yaml":
                subpath = f"/overlays/{render_params['env']}"

            dest_file = f"{template_dest_folder}{subpath}/{dest_relative_file_name}"
            os.makedirs(Path(dest_file).parent, exist_ok=True)

            print(f" processing jinja template {file} -> {dest_file}...")
            template = env.from_string(Path(file).read_text(encoding="utf-8"))
            doc = template.render(render_params)

            with open(dest_file, "w", encoding="utf-8") as dest_file_obj:
                dest_file_obj.write(doc)
                if not doc.endswith("\n"):
                    dest_file_obj.write("\n")

parser = argparse.ArgumentParser(description="Utility script for applying tf outputs to k8s manifests")

parser.add_argument("env", type=str, nargs=1, help="The name of the terraform environment")
parser.add_argument("--tf_input_file", type=str, nargs='+', help="Terraform input files, defaults to './environments/<env>/terraform.tfvars.json'")
parser.add_argument("--tf_output_file", type=str, nargs='+', help="Terraform output files, defaults to the contents of 'tofu output -var-file=environments/<env>/terraform.tfvars.json -json'")
parser.add_argument("--environment_folder", type=str, help="The folder to load environment specific files from, defaults to '.'")
parser.add_argument("--dest_folder", type=str, help="The folder to put the rendered templates in, defaults to the same folder as the source templates")

args = parser.parse_args()
environment_folder = args.environment_folder if args.environment_folder is not None else "."

render_params = {
    'tf': {}
}

env = args.env[0]
print(args)

tf_input_files = args.tf_input_file
if tf_input_files is None or len(tf_input_files) == 0:
    tf_input_files = [f"{environment_folder}/environments/{env}/terraform.tfvars.json"]

tf_output_files = args.tf_output_file
if tf_output_files is None or len(tf_output_files) == 0:
    tf_output_file = "tf_outputs.json"
    cmd_args = [
        "tofu",
        "output",
        f"-var-file={environment_folder}/environments/{env}/terraform.tfvars.json",
        "-json",
        "-show-sensitive"
    ]

    result = subprocess.run(cmd_args, capture_output=True, text=True)

    print(result.stdout)
    
    with open(tf_output_file, 'w', encoding='utf-8') as file:
        file.write(result.stdout)

    tf_output_files = [tf_output_file]


for tf_input_file in tf_input_files:
    print(f"loading params from {tf_input_file}")

    with open(tf_input_file, 'r', encoding='utf-8') as file:
        render_params['tf']['vars'] = json.load(file)


for tf_output_file in tf_output_files:
    print(f"loading outputs from {tf_output_file}")

    with open(tf_output_file, 'r', encoding='utf-8') as file:
        render_params['tf']['outputs'] = json.load(file) 


helio_params_file = f"{environment_folder}/environments/{env}/helio-params.yaml"
with open(helio_params_file, 'r') as file:
    helio_params = yaml.safe_load(file)
    for k, v in helio_params.items():
        render_params[k] = v

max_keys_per_app=9
apps = ['daskhub', 'portal', 'ingress']

api_key_names = ["api_key"]
for i in range(1, max_keys_per_app+1):
    api_key_names.append(f"api_key{i}")

if 'heritage_params' in render_params and \
    'config' in render_params['heritage_params']:
    for app in apps:
        if app in render_params['heritage_params']['config']:
            for api_key_name in api_key_names:
                if api_key_name in render_params['heritage_params']['config'][app]:
                    if render_params['heritage_params']['config'][app][api_key_name] == 'auto':
                        render_params['heritage_params']['config'][app][api_key_name] = secrets.token_hex(SECRET_HEX_IN_BYTES)
                    api_key_as_bytes = bytes.fromhex(render_params['heritage_params']['config'][app][api_key_name])
                    render_params['heritage_params']['config'][app][f"{api_key_name}_base64"] = base64.urlsafe_b64encode(api_key_as_bytes).decode()


render_params['env'] = env

base_dir=Path("./kube").resolve()
dest_folder = args.dest_folder

if dest_folder is not None and dest_folder != "":
    # Install the non-template files and exclude the helm chart artifacts if present
    exclude_extensions = [".j2", ".jinja", '.tgz']
    for src_file in glob.glob(f"{base_dir}/**", recursive=True):
        if src_file.endswith(tuple(exclude_extensions)) or os.path.isdir(src_file):
            continue
        print(src_file)

        relative_path_from_base_dir = Path(src_file).relative_to(base_dir)
        dest_file = Path(dest_folder).joinpath(relative_path_from_base_dir).resolve()

        dest_dir = os.path.dirname(dest_file) or "."
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        shutil.copy2(src_file, dest_file)

for template_src_folder in glob.glob(f"{base_dir}/**/templates", recursive=True):
    if dest_folder is None or dest_folder == "":
        template_dest_folder = Path(f"{template_src_folder}/..").resolve()
    else:
        relative_path_from_base_dir = Path(template_src_folder).relative_to(base_dir)
        template_dest_folder = Path(dest_folder).joinpath(relative_path_from_base_dir.parent).resolve()

    print(f"{template_src_folder} -> {template_dest_folder}")
    apply_jinja_templates_by_dir(template_src_folder, template_dest_folder, render_params)
for template_src_folder in glob.glob(f"{base_dir}/**/jinja_templates", recursive=True):
    if dest_folder is None or dest_folder == "":
        template_dest_folder = Path(f"{template_src_folder}/..").resolve()
    else:
        relative_path_from_base_dir = Path(template_src_folder).relative_to(base_dir)
        template_dest_folder = Path(dest_folder).joinpath(relative_path_from_base_dir.parent).resolve()

    print(f"{template_src_folder} -> {template_dest_folder}")
    apply_jinja_templates_by_dir(template_src_folder, template_dest_folder, render_params)
