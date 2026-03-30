"""
SharedUserBucketStack

Responsible for:
- Surfacing the shared S3 bucket created in BaseAwsStack.
- Providing configuration (bucket name, mount path, prefix) that can be used
  by DaskHub deployment templates to mount S3 at /mnt/s3shared.
"""

from typing import Any, Dict

from aws_cdk import Stack
from constructs import Construct

from base_aws.base_aws_stack import BaseAwsStack


class SharedUserBucketStack(Stack):
    """
    Stack that exposes the shared S3 bucket for users and the desired mount
    configuration (/mnt/s3shared by default).

    NOTE: This stack does NOT create Kubernetes resources directly; instead,
    it exists to:
      - Provide bucket + mount info to other stacks (e.g. DaskhubStack).
      - Keep S3 and mount config decoupled from the base AWS infra.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: Dict[str, Any],
        base_aws: BaseAwsStack,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._config = config
        self._base_aws = base_aws

        user_shared_cfg: Dict[str, Any] = config.get("userSharedBucket", {}) or {}

        # Configurable knobs, with sensible defaults.
        self.mount_enabled: bool = bool(user_shared_cfg.get("mountEnabled", True))
        self.mount_path: str = user_shared_cfg.get("mountPath", "/mnt/s3shared")
        self.bucket_prefix: str = user_shared_cfg.get("bucketPrefix", "")

        # The bucket is actually created by BaseAwsStack; we just reference it.
        self.bucket = base_aws.user_shared_bucket
