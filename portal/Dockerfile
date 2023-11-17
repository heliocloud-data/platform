# syntax = docker/dockerfile:1.2

# Set base image (host OS)
FROM --platform=linux/amd64 python:3.9

# Build Args
# When building behind an https proxy, these build args allow for fetching and installing a
# CA cert. Must also inform pip of the cert file location
ARG ca_cert_url=""

# Args to use with PIP
ARG pip_extra_args=""


# 1: If a ca_cert was provided, update the certificate store
WORKDIR /cert
SHELL ["/bin/bash", "-c"]
RUN if [ "$ca_cert_url" != "" ]; \
    then echo "Installing cert from url ${ca_cert_url}." && \
         curl ${ca_cert_url} -o  /usr/local/share/ca-certificates/CA_CERT.crt && \
         update-ca-certificates --verbose; \
    else echo "No cert update necessary."; \
    fi


# 2: Run the pip installs
WORKDIR /portal
COPY requirements.txt .
SHELL ["/bin/bash", "-c"]
RUN if [ "$ca_cert_url" != "" ]; \
    then pip install --upgrade pip ${pip_extra_args} --cert /etc/ssl/certs/ca-certificates.crt && \
         pip install -r requirements.txt ${pip_extra_args} --cert /etc/ssl/certs/ca-certificates.crt; \
    else pip install --upgrade pip ${pip_extra_args} && \
         pip install -r requirments.txt ${pip_extra_args}; \
    fi

# 3: Setup the portal app to run
COPY app.py .
COPY lib lib/.
COPY static static/.
COPY templates templates/.
RUN ls /portal
CMD [ "python", "-u", "/portal/app.py" ]
