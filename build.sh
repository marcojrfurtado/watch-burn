#!/bin/bash

# This Bash script (1) builds Python dependencies needed to run and deploy
# the demo application and (2) installs the Google App Engine
# developer tools if they aren't found on the system.

# Builds the specified dependency if it hasn't been built. Takes 3 parameters:
#   1. The URL of the git repo.
#   2. The tag name or commit SHA at which to checkout the repo.
#   3. The path within the repo to the library folder.
BuildDep () {
  DST_FOLDER=$(basename "$3")
  echo "Building $DST_FOLDER..."
  if [ ! -d "$DST_FOLDER" ]; then
    # See: http://unix.stackexchange.com/a/84980
    TEMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
    cd "$TEMP_DIR"
    git clone "$1" .
    git checkout "$2" .
    cd -
    mv "$TEMP_DIR/$3" ./
    rm -rf "$TEMP_DIR"
  fi
}

# Build oauth2client.
BuildDep https://github.com/google/oauth2client.git tags/v1.3.2 oauth2client

# Build the Earth Engine Python client library.
BuildDep https://github.com/google/earthengine-api.git v0.1.60 python/ee

# Build httplib2.
BuildDep https://github.com/jcgregorio/httplib2.git tags/v0.9.1 python2/httplib2

# Build Pillow
BuildDep https://github.com/python-pillow/Pillow.git 3.1.x PIL 

# Install the Google App Engine command line tools.
if ! hash dev_appserver.py 2>/dev/null; then
  # Install the `gcloud` command line tool.
  curl https://sdk.cloud.google.com/ | bash
  # Ensure the `gcloud` command is in our path.
  if [ -f ~/.bashrc ]; then
    source ~/.bashrc
  elif [ -f ~/.bash_profile ]; then
    source ~/.bash_profile
  fi
  # Install the Google App Engine command line tools.
  gcloud components update gae-python
fi
