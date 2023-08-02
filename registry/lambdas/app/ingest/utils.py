def get_bucket_name(path: str) -> str:
    """
    Gets the name of the bucket. Assumes names start with one of:
    - file://
    - s3://
    """
    return path.split("/")[2]


def get_bucket_subfolder(path: str) -> str:
    """
    Gets the sub folder within the bucket (everything after the bucket name). Assumes paths starting with:
    - file://
    - s3://
    """
    return "/".join(
        path.split(
            "/",
        )[3:],
    )
