import glob
import os
import jinja2
from jinja2 import Template
from pathlib import Path
import shutil


def apply_jinja_templates_by_dir(
    template_src_folder: str, template_dest_folder: str, render_params: dict
):
    env = jinja2.Environment()

    for file in glob.glob(f"{template_src_folder}/**", recursive=True):
        if os.path.isdir(file):
            continue

        file_relative_to_src_folder = file[len(template_src_folder) + 1 :]
        dest_file = f"{template_dest_folder}/{file_relative_to_src_folder}"
        Path(f"{dest_file}").parent.mkdir(parents=True, exist_ok=True)

        if file.endswith(".j2"):
            # Fix the path...
            dest_file = f"{template_dest_folder}/{os.path.splitext(file_relative_to_src_folder)[0]}"

            print(f" processing jinja template {file}...")
            t = env.from_string(Path(file).read_text())
            doc = t.render(render_params)

            with open(dest_file, "w") as dest_file_obj:
                dest_file_obj.write(doc)
        else:
            # copy the file
            # print(f"{file} -> {dest_file}")
            shutil.copyfile(file, dest_file)
