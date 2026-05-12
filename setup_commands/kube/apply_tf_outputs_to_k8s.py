"""
Utils for working with Jinja templates.
"""

import glob
from pathlib import Path

import jinja2
import json
import os
import secrets
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

render_params = {
    'tf': {}
}

env = "dev" # TODO make command-line arg

# TODO: Auto-wire
with open("tf_inputs.json", 'r', encoding='utf-8') as file:
    render_params['tf']['vars'] = json.load(file) 

# TODO: Auto-wire
with open("tf_outputs.json", 'r', encoding='utf-8') as file:
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
    print("!!!!")
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
