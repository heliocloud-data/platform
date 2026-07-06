import os

from pathlib import Path

import dpath
import re
import shutil
import subprocess

from ruamel.yaml import YAML

def delete_workspace(local_workspace_path):
    if os.path.exists(local_workspace_path):
        shutil.rmtree(local_workspace_path)

def prepare_workspace(local_workspace_path, environment_folder, environment_name):
    # We should generate
    print("Preparing workspace...")

    print(f"Ensuring Local Workspace {local_workspace_path} exists...")
    os.makedirs(Path(local_workspace_path).parent.absolute(), 0o777, True)

    result = subprocess.run(
        [
            "python",
            "./setup_commands/kube/apply_tf_outputs_to_k8s.py",
            f"--environment_folder={environment_folder}/",
            f"--dest_folder={local_workspace_path}/",
            f"--tf_input_file={environment_folder}/environments/{environment_name}/terraform.tfvars.json",
            f"--tf_output_file={environment_folder}/environments/{environment_name}/tf_outputs.json",
            environment_name
        ],
        capture_output=True, text=True, check=False)

    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        raise Exception(f"apply_tf_outputs_to_k8s failed with return code {result.returncode}")

def run_kustomize(kustomization_dir, output_file):
    os.makedirs(Path(output_file).parent.absolute(), 0o777, True)

    cmd = f"kustomize build {kustomization_dir} > {output_file}"
    os.system(cmd)

def run_helm_template(name, chart, chart_version=None, namespace=None, values_files=None, post_render_hook=None, wd=None, extra_opts=None, output_file=None):
    os.makedirs(Path(output_file).parent.absolute(), 0o777, True)

    helm_cmd = f"helm template {name} {chart}"

    cwd = None

    abs_output_file = Path(output_file).absolute()
    try:
        if wd is not None and wd != "":
            cwd = os.getcwd()
            os.chdir(wd)

        if chart == "./":
            os.system(f"helm dep update")


        if chart_version is not None:
            helm_cmd = f"{helm_cmd} --version={chart_version}"

        if namespace is not None:
            helm_cmd = f"{helm_cmd} --namespace={namespace}"

        for values_file in values_files:
            helm_cmd = f"{helm_cmd} --values={values_file}"

        if post_render_hook is not None and post_render_hook != "":
            os.system(f"chmod 755 {post_render_hook}")
        if post_render_hook is not None and post_render_hook != "":
            helm_cmd = f"{helm_cmd} --post-renderer={post_render_hook}"

        if extra_opts is not None and extra_opts != "":
            helm_cmd = f"{helm_cmd} {extra_opts}"

        helm_cmd = f"{helm_cmd} > {abs_output_file}"
        os.system(helm_cmd)
    except Exception as e:
        raise e
    finally:
        if cwd is not None:
            os.chdir(cwd)


def sanitize_snapshots(input_file, output_file, values_to_remove_from_snapshot):
    with open(input_file, "r") as f:
        with open(output_file, "w") as of:
            contents = f.read()
            contents_arr = contents.split("---")

            for doc_as_string in contents_arr:
                if doc_as_string is None:
                    continue

                # To keep the diffs to a minimum, replace the names of stuff.
                doc_as_string = doc_as_string.replace(
                    "heliocloud-daskhub/charts/daskhub/charts/jupyterhub",
                    "daskhub/charts/jupyterhub",
                )
                doc_as_string = doc_as_string.replace(
                    "daskhub/charts/daskhub/charts/jupyterhub",
                    "daskhub/charts/jupyterhub",
                )
                doc_as_string = doc_as_string.replace("heliocloud-daskhub", "daskhub")
                # Fix the funny issue w/ the JSON doc as string
                doc_as_string = re.sub(
                    "_PROPERTIES = .*",
                    r'_PROPERTIES = json.loads("{}") # CLEANED FOR TESTING',
                    doc_as_string,
                )
                # Remove the rolling checksums
                doc_as_string = re.sub(
                    "checksum[/]configmap[:] (.*)",
                    r'checksum/configmap: "0000" # CLEANED FOR TESTING',
                    doc_as_string,
                )

                yaml = YAML()

                elem_as_yaml = yaml.load(doc_as_string)
                if elem_as_yaml is None:
                    continue

                # 4 spaces then 8 spaces if 'data' in elem_as_yaml and
                # 'hub.config.JupyterHub.cookie_secret' in elem_as_yaml['data']: elem_as_yaml[
                # 'data']['hub.config.JupyterHub.cookie_secret'] = "__REMOVED_FROM_OUTPUT__"
                for value_to_remove_from_snapshot in values_to_remove_from_snapshot:
                    try:
                        obj = dpath.get(elem_as_yaml, value_to_remove_from_snapshot)
                        dpath.delete(elem_as_yaml, value_to_remove_from_snapshot)
                    except:
                        pass

                of.write("---\n")
                yaml.indent(mapping=2, sequence=4, offset=2)
                yaml.dump(elem_as_yaml, of)
