FROM ghcr.io/opentofu/opentofu:minimal AS tofu

FROM python:3.13.2

# Copy the tofu binary
COPY --from=tofu /usr/local/bin/tofu /usr/local/bin/tofu

ARG DEV_CONTAINER_USER=''

RUN \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      sudo \
      git \
      curl \
    && useradd -m $DEV_CONTAINER_USER \
    && echo $DEV_CONTAINER_USER ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$DEV_CONTAINER_USER \
    && chmod 0440 /etc/sudoers.d/$DEV_CONTAINER_USER


USER $DEV_CONTAINER_USER

# Add user python bin is on the path
ENV PATH=${HOME}/.local/bin:${PATH}
