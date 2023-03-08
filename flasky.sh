#!/usr/bin/env bash

#set -x
set -e

HOME_PATH=$(eval echo ~${SUDO_USER})
SCRIPT_FILE=$(basename $(readlink -f "${0}"))
SCRIPT_PATH=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

if [ ${#} -eq 0 ]; then
    OPTION='run'
else
    OPTION=${1}
fi

WORK_PATH=${SCRIPT_PATH}
PYTHON_ENV=${HOME_PATH}/python_env/bin/activate
EXEC_FILE=${SCRIPT_PATH}/app.py
TRAVERSE_PATH=${SCRIPT_PATH}

function clean () {
    find ${SCRIPT_PATH} -type d -name '__pycache__' -exec rm -rf {} +
    find ${SCRIPT_PATH} -type f -name '*.log' -delete
    find ${SCRIPT_PATH} -type f -name '*.db' -delete
}

if [[ ${#} -eq 0 || ${OPTION} == 'run' ]]; then
    cd ${WORK_PATH}
    source ${PYTHON_ENV}
    python3 ${EXEC_FILE}
elif [ ${OPTION} == 'clean' ]; then
    clean
elif [ ${OPTION} == 'init' ]; then
    sudo apt install libgl1 -y
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    pip3 install -r ${SCRIPT_PATH}/requirements.txt
    flask init
elif [ ${OPTION} == 'test' ]; then
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    flask test
elif [ ${OPTION} == 'deploy' ]; then
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    nohup gunicorn -w 1 -b 127.0.0.1:4100 'hallelujah:create_app()' > /dev/null 2>&1 &
else
    echo "Usage: ${SCRIPT_FILE} [run|clean|test|init|deploy]"
fi

