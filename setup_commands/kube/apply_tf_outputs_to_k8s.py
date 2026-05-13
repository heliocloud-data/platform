"""
Utils for working with Jinja templates.
"""

import argparse
import glob
from pathlib import Path

import jinja2
import json
import os
import secrets
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
        Path(f"{dest_file}").parent.mkdir(parents=True, exist_ok=True)

        if file.endswith(".j2"):
            dest_relative_file_name = env.from_string(os.path.splitext(file_relative_to_src_folder)[0]).render(render_params)

            subpath = ""
            # Kustomize units 
            if dest_relative_file_name == "kustomization.yaml":
                subpath = f"/overlays/{render_params['env']}"

            dest_file = f"{template_dest_folder}{subpath}/{dest_relative_file_name}"

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

args = parser.parse_args()

render_params = {
    'tf': {}
}

env = args.env[0]
print(args)

tf_input_files = args.tf_input_file
if tf_input_files is None or len(tf_input_files) == 0:
    tf_input_files = [f"./environments/{env}/terraform.tfvars.json"]

tf_output_files = args.tf_output_file
if tf_output_files is None or len(tf_output_files) == 0:
    tf_output_file = "tf_outputs.json"
    cmd_args = [
        "tofu",
        "output",
        f"-var-file=environments/{env}/terraform.tfvars.json",
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


helio_params_file = f"environments/{env}/helio-params.yaml"
with open(helio_params_file, 'r') as file:
    helio_params = yaml.safe_load(file)
    for k, v in helio_params.items():
        render_params[k] = v

# TODO: Once the templates have
if 'heritage_params' in render_params and \
    'config' in render_params['heritage_params'] and \
    'daskhub' in render_params['heritage_params']['config'] and \
    'api_key1' in render_params['heritage_params']['config']['daskhub'] and \
    render_params['heritage_params']['config']['daskhub']['api_key1'] == 'auto':
    render_params['heritage_params']['config']['daskhub']['api_key1'] = secrets.token_hex(SECRET_HEX_IN_BYTES)
render_params['env'] = env

if 'heritage_params' in render_params and \
    'config' in render_params['heritage_params'] and \
    'daskhub' in render_params['heritage_params']['config'] and \
    'api_key2' in render_params['heritage_params']['config']['daskhub'] and \
    render_params['heritage_params']['config']['daskhub']['api_key2'] == 'auto':
    render_params['heritage_params']['config']['daskhub']['api_key2'] = secrets.token_hex(SECRET_HEX_IN_BYTES)
render_params['env'] = env

print(render_params)
base_dir=Path("./kube").resolve()
for template_src_folder in glob.glob(f"{base_dir}/**/templates", recursive=True):
    template_dest_folder = Path(f"{template_src_folder}/..").resolve()
    print(f"{template_src_folder} -> {template_dest_folder}")
    apply_jinja_templates_by_dir(template_src_folder, template_dest_folder, render_params)
for template_src_folder in glob.glob(f"{base_dir}/**/jinja_templates", recursive=True):
    template_dest_folder = Path(f"{template_src_folder}/..").resolve()
    print(f"{template_src_folder} -> {template_dest_folder}")
    apply_jinja_templates_by_dir(template_src_folder, template_dest_folder, render_params)
