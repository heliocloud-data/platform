import argparse
import re
import requests
import sys

from bs4 import BeautifulSoup

# Enable to print the complete document
DEBUG = False

target_k8_minor_version = None

parser = argparse.ArgumentParser(
    prog="HelioCloud Catalog file editor",
    description="Allows for direct editing of catalog.json files on local disk.",
)
parser.add_argument(
    "-t",
    "--target-k8-minor-version",
    type=str,
    required=True,
    help="Name of the catalog file to load.",
)
parser.add_argument(
    "-o", "--output-file", type=str, required=True, help="Name of the catalog file to load."
)

args = parser.parse_args()
target_k8_minor_version = args.target_k8_minor_version
target_platform = "linux/amd64"
output_file = args.output_file

doc_site_url = "https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html"

regex = rf"curl\s+.*(https[:][/][/].*[/]({target_k8_minor_version}[.][0-9]+)[/]([0-9]+[-][0-9]+[-][0-9]+)[/]bin[/]{target_platform}[/]kubectl)"

r = requests.get(doc_site_url)

soup = BeautifulSoup(
    r.content, "html5lib"
)  # If this line causes an error, run 'pip install html5lib' or install html5lib

if DEBUG:
    print(soup.prettify())

kubectl_download_url = None
kubectl_version = None
for row in soup.findAll("code", attrs={"class": "bash"}):
    m = re.fullmatch(regex, row.text)
    if m is not None:
        kubectl_download_url = m.group(1)
        kubectl_version = m.group(2)

if kubectl_download_url is None:
    print(
        f"error: unable to locate kubectl_download_url from AWS doc site, navigate to {doc_site_url} and make sure there's a download link for your Kubernetes version ({target_k8_minor_version})"
    )
    sys.exit(1)
    raise

print(
    f"Found download URL ({kubectl_download_url}) for Kubernetes minor version ({target_k8_minor_version})"
)

with open(output_file, "w", encoding="utf-8") as file:
    file.write(f"NEW_K8_VERSION={target_k8_minor_version}\n")
    file.write(f"NEW_URL={kubectl_download_url}\n")
