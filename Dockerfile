## Template project uses python image provided by Microsoft. It contains additional tools for
## development, such as pylint, flake8, etc.
## If team elects to use different image, this file should be updated accordingly. Example for
## using official node: `FROM node:14-bullseye`
## You can find devcontainer templates for other languages here:
## https://github.com/microsoft/vscode-dev-containers/tree/main/containers

## It would be smart to separate development stuff from production stuff, but for now
## this is enough (fore-shadowing).
## How to create deriative/multi-stage image: https://docs.docker.com/build/building/multi-stage/
FROM mcr.microsoft.com/vscode/devcontainers/python:3.10-bullseye

## [Optional] Look into using jemalloc with python for more efficient memory management

## Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

## Set static working directory. By default, it is set to /workspaces/<project-name> by
## vscode.
WORKDIR /app

## Declare default flask app as environment variable
## https://flask.palletsprojects.com/en/2.2.x/cli/
ARG FLASK_APP=tjts5901.app
ENV FLASK_APP=${FLASK_APP}

## Setup the default port for flask to listen on
ARG FLASK_RUN_PORT=5001
ENV FLASK_RUN_PORT=${FLASK_RUN_PORT}

## Run Flask app when container started, and listen all the interfaces
## Note: CMD doesn't run command in build, but defines an starting command
## when container is started (or arguments for ENTRYPOINT).
CMD flask run --host=0.0.0.0 # --port=${FLASK_RUN_PORT} --app=${FLASK_APP}

## Examples for other commands:
## Run nothing, so that the container can be used as a base image
#CMD ["bash", "-c", "sleep infinity"]
## Run Flask app using Gunicorn, which unlike Flask, doesn't complain about being development thing.
#CMD gunicorn --bind "0.0.0.0:${PORT}"" tjts5901.app:app

## Install requirements using pip. This is done before copying the app, so that
## requirements layer is cached. This way, if app code changes, only app code is
## copied, and requirements are not re-installed.
COPY requirements.txt /tmp/pip-tmp/
RUN pip --disable-pip-version-check install -r /tmp/pip-tmp/requirements.txt && \
    rm -rf /tmp/pip-tmp

## Copy app to WORKDIR folder
COPY . .

## Install self as editable (`-e`) module. In a long run it would be recommeded
## to remove `COPY` and only install app as a package.
RUN pip --disable-pip-version-check install -v -e .

## If defined, copy commit id to app environment. This is used to identify
## which version of the app is running.
ARG CI_COMMIT_SHA
ENV CI_COMMIT_SHA=${CI_COMMIT_SHA}

## Save build date and time
RUN echo "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> /app/.env

## To prevent vscode constantly re-installing extensions, we need to create a folder for it.
## In devcontainer.json, we mount volume to this folder so that extensions are not lost.
## Create vscode extension folder, and change ownership of it.
ARG USERNAME=vscode
RUN test ! -z "${USERNAME}" && mkdir -p /home/${USERNAME}/.vscode-server/extensions && \
    chown -R $USERNAME /home/$USERNAME/.vscode-server

## [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

## [Optional] Uncomment this line to install global node packages.
# RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g <your-package-here>" 2>&1
