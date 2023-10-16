# syntax = docker/dockerfile:1.2

# Set base image (host OS)
FROM --platform=linux/amd64 python:3.9

# The path to the local directory where the CA certificate should be saved.
ARG PORTAL_LOCAL_CERT_PATH="/usr/local/share/ca-certificates"

# The URL to the CA certificate, if empty, no CA certificate will be installed.
ARG PORTAL_CA_CERT=""

# Additional arguments to the pip3 command.  On occasion, more secure networks
# will require lax timeouts and/or retries.
ARG PORTAL_PIP_EXTRA_ARGS=""

# If the caller provides 'PORTAL_CA_CERT', we should install the provided
# certificate.  If it's blank, which is the default, this step does nothing.
RUN \
  if [ "${PORTAL_CA_CERT}" = "" ] ; then \
    exit 0 ; \
  fi ; \
  echo "Installing certificate ${PORTAL_CA_CERT}" to ${PORTAL_LOCAL_CERT_PATH} ; \
  PORTAL_CA_CERT_BASENAME=$(basename ${PORTAL_CA_CERT}) ; \
  PORTAL_CA_CERT_FILENAME=${PORTAL_CA_CERT_BASENAME%.*}.crt ; \
  curl ${PORTAL_CA_CERT} -o "${PORTAL_LOCAL_CERT_PATH}/${PORTAL_CA_CERT_FILENAME}" ; \
  update-ca-certificates

# Set the working directory in the container
WORKDIR /app

RUN pwd
# Copy the dependencies file to the working directory
COPY ./portal/requirements.txt .

# Install any dependencies
RUN \
  if [ "${PORTAL_CA_CERT}" != "" ] ; then \
    PORTAL_CA_CERT_BASENAME=$(basename ${PORTAL_CA_CERT}) ; \
    PORTAL_CA_CERT_FILENAME=${PORTAL_CA_CERT_BASENAME%.*}.crt ; \
    PIP_INSTALL_EXTRA_OPTS="--cert ${PORTAL_LOCAL_CERT_PATH}/${PORTAL_CA_CERT_FILENAME}" ; \
  fi ; \
  pip3 install -r requirements.txt ${PIP_INSTALL_EXTRA_OPTS} ${PORTAL_PIP_EXTRA_ARGS}

# Copy the content of the local src directory to the working directory
COPY ./portal .

# Specify the command to run on container start
CMD [ "python", "-u", "./app.py" ]