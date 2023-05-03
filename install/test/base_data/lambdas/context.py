import os
import sys


dirname = os.path.dirname(__file__)
path = os.path.join(dirname, "..")
abs_path = os.path.abspath(path)
sys.path.insert(0, os.path.abspath(path))

import base_data.lambdas.app as lambdas_app

