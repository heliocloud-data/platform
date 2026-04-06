export PYTHONPATH=.:test/unit
pytest -c pytest-unit.ini --debug --verbose $@
