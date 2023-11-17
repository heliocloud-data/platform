"""
Contains utility functions to support unit testing.
"""
import os
from pathlib import Path

import dpath
from ruamel.yaml import YAML


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
