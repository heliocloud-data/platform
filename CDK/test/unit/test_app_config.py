import pytest
from app_config import load_configs


def test_load_configs():
    cfg = load_configs("test/unit/resources/test_app_config/instance", "test_config")

    print(f"AAA-> {cfg}")

    # Confirm values in the instance document
    assert cfg["env"]["account"] == 123456789
    assert cfg["env"]["region"] == "us-east-100"
    assert cfg["enabled"]["registry"] == True
    assert cfg["registry"]["datasetBucketNames"][0] == "suds-datasets-1"
    assert cfg["registry"]["ingestBucketName"] == "acid-reflux"

    assert cfg["auth"]["domain_prefix"] == "apl-helio"
    assert cfg["portal"]["domain_url"] is None
    assert cfg["portal"]["domain_record"] is None
    assert cfg["portal"]["domain_certificate_arn"] is None
    assert cfg["daskhub"] is None


def test_load_configs_null_basedir():
    """
    Should load a default configuration
    """
    cfg = load_configs(hc_id="example")

    # Confirm values in the instance document
    assert cfg["env"]["account"] == 12345678


def test_load_configs_missing_file():
    """
    Confirm FileNotFoundError thrown if a non-existant configuration file is referenced.
    """
    with pytest.raises(FileNotFoundError):
        load_configs("test/unit/resources/test_app_config/instance", "DoesNotExist")
        print("FileNotFoundError should be thrown.")
        assert False


def test_method_load_configs_InvalidFile():
    """
    Confirm a ValueError is thrown if an invalid configuration file is supplied
    """
    with pytest.raises(ValueError):
        load_configs("test/unit/resources/test_app_config/instance", "invalid")
        print("ValueError should be thrown")
        assert False
