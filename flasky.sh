#!/usr/bin/env bash
#set -x
set -e

HOME_PATH=$(eval echo ~${SUDO_USER})
SCRIPT_FILE=$(basename $(readlink -f "${0}"))
SCRIPT_PATH=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

if [[ ${#} -eq 0 ]]; then
    OPTION='help'
else
    OPTION=${1}
fi

NUM_WORKERS=$(($(nproc) * 2 + 1))
WORK_PATH=${SCRIPT_PATH}
PYTHON_PATH=${HOME_PATH}/.python_env
PYTHON_ENV=${PYTHON_PATH}/bin/activate
EXEC_FILE=${SCRIPT_PATH}/app.py
TRAVERSE_PATH=${SCRIPT_PATH}
APP_NAME=hallelujah
SERVICE_PATH=/etc/systemd/system
SERVICE_NAME=${APP_NAME}.service

function clean () {
    find ${SCRIPT_PATH} -type d -name '__pycache__' -exec rm -rf {} +
    find ${SCRIPT_PATH} -type f -name '*.log*' -delete
    find ${SCRIPT_PATH} -type f -name '*.db' -delete
}

function cron_add () {
    read -p "input backup server: " BACKUP_SERVER
    CRON_JOB="0 1 * * 1 ${SCRIPT_PATH}/${SCRIPT_FILE} cron $(whoami) ${BACKUP_SERVER}"
    if crontab -l 2>/dev/null | grep -Fq "${CRON_JOB}"; then
        crontab -l | grep -Fv "${CRON_JOB}" | crontab -
    fi

    if [[ -z "$(crontab -l)" ]]; then
        echo "${CRON_JOB}" | crontab -
    else
        (echo "$(crontab -l)"; echo "${CRON_JOB}") | crontab -
    fi
}

function cron_job () {
    BACKUP_USER=${1}
    BACKUP_SERVER=${2}
    DATA_PATH="${HOME_PATH}/data"
    DB_FILE="${DATA_PATH}/${APP_NAME}.sql"
    BACKUP_PATH="${HOME_PATH}/backup"
    BACKUP_FILE="data_$(date +"%Y%m%d_%H%M%S").tar.gz"
    KEEP_CNT=2

    function clean () {
        cd "${BACKUP_PATH}" || exit
        DELETE_LIST=$(ls -1 "${BACKUP_PATH}" | sort | head -n -${KEEP_CNT})
        for DELETE_FILE in ${DELETE_LIST}; do
            rm -f "${BACKUP_PATH}/${DELETE_FILE}"
            ssh "${BACKUP_USER}@${BACKUP_SERVER}" "rm -f '${BACKUP_PATH}/${DELETE_FILE}'"
        done
        cd -
    }

    function backup () {
        rm -f ${DATA_PATH}/${DB_FILE}
        ${SCRIPT_PATH}/${SCRIPT_FILE} backup
        cd ${DATA_PATH}/.. && tar -zcf "${BACKUP_PATH}/${BACKUP_FILE}" "$(basename ${DATA_PATH})"
    }

    function sync () {
        scp "${BACKUP_PATH}/${BACKUP_FILE}" "${BACKUP_USR}@${BACKUP_SERVER}:${BACKUP_PATH}/"
        ssh "${BACKUP_USER}@${BACKUP_SERVER}" "sudo service ${APP_NAME} stop"
        ssh "${BACKUP_USER}@${BACKUP_SERVER}" "rm -rf ${DATA_PATH}/*"
        ssh "${BACKUP_USER}@${BACKUP_SERVER}" "cd ${DATA_PATH}/..; tar -zxf ${BACKUP_PATH}/${BACKUP_FILE}"
        ssh "${BACKUP_USER}@${BACKUP_SERVER}" "${SCRIPT_PATH}/${SCRIPT_FILE} restore"
        ssh "${BACKUP_USER}@${BACKUP_SERVER}" "cd ${SCRIPT_PATH}; git clean -xdf; git checkout .; git pull"
        ssh "${BACKUP_USER}@${BACKUP_SERVER}" "sudo service ${APP_NAME} start"
    }

    clean
    backup
    sync
}

if [[ ${#} -eq 0 || ${OPTION} == 'debug' ]]; then
    cd ${WORK_PATH}
    source ${PYTHON_ENV}
    python3 ${EXEC_FILE}
elif [ ${OPTION} == 'clean' ]; then
    cd ${WORK_PATH}
    clean
elif [ ${OPTION} == 'init' ]; then
    sudo apt install libgl1 -y
    cd ${SCRIPT_PATH}
    mkdir -p ${PYTHON_PATH}
    virtualenv ${PYTHON_PATH}
    source ${PYTHON_ENV}
    pip3 install -r ${SCRIPT_PATH}/requirements.txt
    if [[ ${#} -eq 5 ]]; then
        flask init --mail_address ${3} --mail_password ${5}
    else
        echo "${SCRIPT_FILE} init --mail_address EMAIL_ADDRESS --mail_password EMAIL_PASSWORD"
        exit 0
    fi
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
elif [ ${OPTION} == 'cron' ]; then
    if [[ ${#} -ne 3 ]]; then
        cron_add
    else
        cron_job ${2} ${3}
    fi
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
    echo "Usage: ${SCRIPT_FILE} [init|debug|run|deploy|cron|test|clean|addusr|delusr|backup|restore]"
fi

