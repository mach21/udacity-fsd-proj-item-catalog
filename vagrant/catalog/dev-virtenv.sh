#!/bin/bash

VIRTENV_SETUP_SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo --- VIRTENV_SETUP_SCRIPT_PATH is "$VIRTENV_SETUP_SCRIPT_PATH"
if [ -z "$VIRTENV_PATH" ]; then
	VIRTENV_PATH="${VIRTENV_SETUP_SCRIPT_PATH}/.virtenv"
fi

if [ ! -d "$VIRTENV_PATH" ];
then
    echo --- virtualenv directory "$VIRTENV_PATH" does not exist, will create
    python3 -m virtualenv -p python3 "$VIRTENV_PATH" --always-copy
fi

echo --- activating virtual env in "$VIRTENV_PATH"
source "$VIRTENV_PATH"/bin/activate

echo --- installing requirements
pip3 install -r ${VIRTENV_SETUP_SCRIPT_PATH}/requirements.txt

# pip install failed -> complain
if [[ $? -ne 0 ]] ; then
    exit 1
fi

unset VIRTENV_SETUP_SCRIPT_PATH
unset VIRTENV_PATH