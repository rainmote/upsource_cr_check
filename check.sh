#!/bin/bash

set -x

export UPSOURCE_ENDPOINT="https://xxx.domain"
export UPSOURCE_USERNAME="admin"
export UPSOURCE_PASSWORD="passwd"
export UPSOURCE_PROJECT="projectA"

DIR=$(dirname "$0")
PYTHON3=$(/usr/bin/env python3)
SRC_DIR="$DIR"/code_review

# install python deps lib
sudo "$PYTHON3" -m pip install -r "$SRC_DIR"/requirements.txt

$PYTHON3 "$SRC_DIR"/check.py