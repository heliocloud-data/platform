"""
Contains various functions for interacting with heliocloud
configurations.
"""
from app_config import load_configs


def get_portal_url(hc_instance):
    """
    Get the base URL of portal.
    """
    cfg = load_configs(hc_id=hc_instance)

    return f"https://{cfg['portal']['domain_record']}.{cfg['portal']['domain_url']}"
