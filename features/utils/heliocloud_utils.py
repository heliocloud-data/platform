"""
Contains various functions for interacting with heliocloud
configurations.
"""
from app_config import load_configs

# pylint: disable=line-too-long


def get_base_url(hc_instance, app):
    """
    Get the base URL for a given application
    """
    if app == "portal":
        return get_portal_url(hc_instance)
    if app == "daskhub":
        return get_daskhub_url(hc_instance)
    raise ValueError(f"Unrecognized app {app}")


def get_portal_url(hc_instance):
    """
    Get the base URL of portal.
    """
    cfg = load_configs(hc_id=hc_instance)

    return f"https://{cfg['portal']['domain_record']}.{cfg['portal']['domain_url']}"


def get_daskhub_url(hc_instance):
    """
    Get the base URL of daskhub.
    """
    cfg = load_configs(hc_id=hc_instance)

    return f"https://{cfg['daskhub']['ROUTE53_DASKHUB_PREFIX']}.{cfg['daskhub']['ROUTE53_HOSTED_ZONE']}"
