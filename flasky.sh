#!/usr/bin/env bash
#set -x
set -e

HOME_PATH=$(eval echo ~${SUDO_USER})
SCRIPT_FILE=$(basename $(readlink -f "${0}"))
SCRIPT_PATH=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

if [[ ${#} -eq 0 ]]; then
    OPTION='run'
else
    OPTION=${1}
fi

NUM_WORKERS=$(nproc)
WORK_PATH=${SCRIPT_PATH}
PYTHON_PATH=${HOME_PATH}/python_env
PYTHON_ENV=${PYTHON_PATH}/bin/activate
EXEC_FILE=${SCRIPT_PATH}/app.py
TRAVERSE_PATH=${SCRIPT_PATH}
SERVICE_PATH=/etc/systemd/system
SERVICE_NAME=hallelujah.service

function clean () {
    find ${SCRIPT_PATH} -type d -name '__pycache__' -exec rm -rf {} +
    find ${SCRIPT_PATH} -type f -name '*.log*' -delete
    find ${SCRIPT_PATH} -type f -name '*.db' -delete
}

if [[ ${#} -eq 0 || ${OPTION} == 'debug' ]]; then
    cd ${WORK_PATH}
    source ${PYTHON_ENV}
    python3 ${EXEC_FILE}
elif [ ${OPTION} == 'clean' ]; then
    clean
elif [ ${OPTION} == 'init' ]; then
    if [[ ${#} -ne 5 ]]; then
        echo "${SCRIPT_FILE} init --mail_address EMAIL_ADDRESS --mail_password EMAIL_PASSWORD"
        exit -1
    fi
    sudo apt install libgl1 -y
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    pip3 install -r ${SCRIPT_PATH}/requirements.txt
    flask init --mail_address ${3} --mail_password ${5}
elif [ ${OPTION} == 'addusr' ]; then
    if [[ ${#} -ne 5 ]]; then
        echo "${SCRIPT_FILE} addusr --username USERNAME --password PASSWORD"
        exit -1
    fi
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    flask addusr --username ${3} --password ${5}
elif [ ${OPTION} == 'delusr' ]; then
    if [[ ${#} -ne 3 ]]; then
        echo "${SCRIPT_FILE} delusr --username"
        exit -1
    fi
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    flask delusr --username ${3}
elif [ ${OPTION} == 'test' ]; then
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    flask test
elif [ ${OPTION} == 'deploy' ]; then
    sudo cp ${SCRIPT_PATH}/service.conf ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|USER_NAME|${USER}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|PROJECT_PATH|${SCRIPT_PATH}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|PYTHON_PATH|${PYTHON_PATH}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|NUM_WORKERS|${NUM_WORKERS}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    SECRET_KEY=$(echo ${RANDOM} | md5sum | head -c 32)
    sudo sed -i "s|SECRET_KEY = .*|SECRET_KEY = '${SECRET_KEY}'|g" ${SCRIPT_PATH}/hallelujah/config.py
    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    sudo systemctl restart ${SERVICE_NAME}
elif [ ${OPTION} == 'run' ]; then
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    nohup gunicorn -w 1 -b 127.0.0.1:4100 'hallelujah:create_app()' > /dev/null 2>&1 &
elif [ ${OPTION} == 'backup' ]; then
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    flask backup
elif [ ${OPTION} == 'restore' ]; then
    cd ${SCRIPT_PATH}
    source ${PYTHON_ENV}
    flask restore
else
    echo "Usage: ${SCRIPT_FILE} [init|debug|run|deploy|test|clean|addusr|delusr|backup|restore]"
fi

