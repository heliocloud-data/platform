FROM python:3.9
ARG DEV_CONTAINER_USER=''

RUN \
    apt-get update && apt-get install -y sudo && \
    useradd -m $DEV_CONTAINER_USER \
    && echo $DEV_CONTAINER_USER ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$DEV_CONTAINER_USER \
    && chmod 0440 /etc/sudoers.d/$DEV_CONTAINER_USER

USER $DEV_CONTAINER_USER
