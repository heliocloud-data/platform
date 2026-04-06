"""
Contains utility functions to support unit testing.
"""
import os
import re
import dpath
from ruamel.yaml import YAML

HELM_OPT_KUBE_VERSION = "1.29"
HELM_OPT_API_VERSION = "1.29"

PATH_TO_RESOURCES = f"{os.path.dirname(__file__)}/resources"


def which(program):
    """
    This function provides the location of an executable that *should be on the
    path.  This is ultimately used to determine if 'node' is installed in the
    environment, which is a requirement for all tests within this file.
    """
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


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


def create_dumpfile(test_class: str, test_name: str, data: str, dump_dir=None) -> None:
    """
    Creates a dumpfile named for the test_class and test_testname provided, stored in dump_dir.
    File will be named:  dumpdir/test_class/test_name.dump

    If dump_dir is left None (default),  it will be placed in /temp of the platform codebase.
    """
    if dump_dir is None:
        dump_dir = "temp/test/unit/dumpfiles/"

    dump_file = f"{dump_dir}/{test_class}/{test_name}.dump"
    os.makedirs(os.path.dirname(dump_file), exist_ok=True)
    with open(dump_file, mode="w") as df_handle:
        df_handle.write(data)


def do_execute_helm_template(snapshot, params: dict):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """
    values_to_remove_from_snapshot = params["values_to_remove_from_snapshot"]

    name = params["repo_name"]
    chart = params["chart"]["name"]
    chart_version = None
    namespace = params["namespace"]
    extra_ops = params["extra_opts"]

    if "version" in params["chart"]:
        chart_version = params["chart"]["version"]

    output_filename = params["output_filename"]
    output_file_original = os.path.abspath(f"temp/test_helm_templating/ORIGINAL-{output_filename}")
    output_file_cleaned = os.path.abspath(f"temp/test_helm_templating/CLEANED-{output_filename}")
    values = params["values"]

    helm_cmd = f"helm template {name} {chart} --api-versions={HELM_OPT_API_VERSION} --api-versions={HELM_OPT_KUBE_VERSION} --namespace={namespace}"

    if chart == "./":
        helm_cmd = f"helm dep update && {helm_cmd}"
    if chart_version is not None:
        helm_cmd = f"{helm_cmd} --version={chart_version}"

    if "post_render_hook" in params and params["post_render_hook"] != "":
        helm_cmd = f"chmod 755 {params['post_render_hook']} && {helm_cmd}"

    if "wd" in params and params["wd"] != "":
        helm_cmd = f"cd {params['wd']} && pwd && {helm_cmd}"
    for value in values:
        helm_cmd = f"{helm_cmd} --values={value}"

    if "post_render_hook" in params and params["post_render_hook"] != "":
        helm_cmd = f"{helm_cmd} --post-renderer={params['post_render_hook']}"

    helm_cmd = f"{helm_cmd} {extra_ops}"

    # Write the file
    cmd = f"{helm_cmd} > {output_file_original}"
    print(cmd)

    os.makedirs(os.path.dirname(output_file_original), exist_ok=True)
    os.system(cmd)

    # Clean the file, by removing any non-deterministic settings that will change run-to-run
    sanitize_snapshots(output_file_original, output_file_cleaned, values_to_remove_from_snapshot)

    snapshot.snapshot_dir = f"{PATH_TO_RESOURCES}/test_helm_templating/snapshots"
    with open(output_file_cleaned, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, output_filename)


def do_execute_kustomize(snapshot, test_name, params: dict):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """
    values_to_remove_from_snapshot = params["values_to_remove_from_snapshot"]

    overlay_path = params["overlay_path"]
    extra_ops = params["extra_opts"]

    output_filename = params["output_filename"]
    output_file_original = os.path.abspath(f"temp/{test_name}/ORIGINAL-{output_filename}")
    output_file_cleaned = os.path.abspath(f"temp/{test_name}/CLEANED-{output_filename}")

    kustomize_cmd = f"kustomize build {overlay_path}"

    if "wd" in params and params["wd"] != "":
        kustomize_cmd = f"cd {params['wd']} && pwd && {kustomize_cmd}"

    kustomize_cmd = f"{kustomize_cmd} {extra_ops}"

    # Write the file
    cmd = f"{kustomize_cmd} > {output_file_original}"
    print(cmd)

    os.makedirs(os.path.dirname(output_file_original), exist_ok=True)
    os.system(cmd)

    # Clean the file, by removing any non-deterministic settings that will change run-to-run
    sanitize_snapshots(output_file_original, output_file_cleaned, values_to_remove_from_snapshot)

    snapshot.snapshot_dir = f"{PATH_TO_RESOURCES}/{test_name}/snapshots"
    with open(output_file_cleaned, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, output_filename)
