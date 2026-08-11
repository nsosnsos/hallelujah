#!/usr/bin/env bash
#set -x
set -e

CUR_USER="${SUDO_USER:-$(whoami)}"
HOME_PATH="/home/${CUR_USER}"
SCRIPT_FILE=$(basename $(readlink -f "${0}"))
SCRIPT_PATH=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

NUM_WORKERS=$(($(nproc) + 1))
PYTHON_PATH=${HOME_PATH}/.python_env
PYTHON_ENV=${PYTHON_PATH}/bin/activate
EXEC_FILE=${SCRIPT_PATH}/app.py
APP_NAME=hallelujah
SERVICE_PATH=/etc/systemd/system
SERVICE_NAME=${APP_NAME}.service
DATA_PATH="${HOME_PATH}/data"
BACKUP_PATH="${HOME_PATH}/backup"
KEEP_CNT=1

if [[ ${#} -eq 0 ]]; then
    OPTION='help'
else
    OPTION=${1}
fi


function code_clean () {
    find ${SCRIPT_PATH} -type d -name '__pycache__' -exec rm -rf {} +
    find ${SCRIPT_PATH} -type f -name '*.log*' -delete
    find ${SCRIPT_PATH} -type f -name '*.db' -delete
}

function cron_add_backup () {
    CRON_JOB="0 2 * * * ${SCRIPT_PATH}/${SCRIPT_FILE} cron job_backup"
    if crontab -l 2>/dev/null | grep -Fq "${CRON_JOB}"; then
        crontab -l | grep -Fv "${CRON_JOB}" | crontab -
    fi

    if [[ -z "$(crontab -l)" ]]; then
        echo "${CRON_JOB}" | crontab -
    else
        (echo "$(crontab -l)"; echo "${CRON_JOB}") | crontab -
    fi
}

function cron_job_backup () {
    DB_FILE="${APP_NAME}.sql"
    BACKUP_FILE="data_$(date +"%Y%m%d_%H%M%S").tar.gz"

    function clean () {
        cd "${BACKUP_PATH}" || exit
        DELETE_LIST=$(ls -1 "${BACKUP_PATH}" | sort | head -n -${KEEP_CNT})
        for DELETE_FILE in ${DELETE_LIST}; do
            rm -f "${BACKUP_PATH}/${DELETE_FILE}"
        done
        cd -
    }

    function backup () {
        rm -f ${DATA_PATH}/${DB_FILE}
        ${SCRIPT_PATH}/${SCRIPT_FILE} backup
        cd ${DATA_PATH}/.. && tar -zcf "${BACKUP_PATH}/${BACKUP_FILE}" "$(basename ${DATA_PATH})"
    }

    clean
    backup
}

function cron_add_sync_push () {
    REMOTE_USER=${1}
    REMOTE_HOST=${2}
    CRON_JOB="0 3 * * 1 ${SCRIPT_PATH}/${SCRIPT_FILE} cron job_sync_push ${REMOTE_USER} ${REMOTE_HOST}"
    if crontab -l 2>/dev/null | grep -Fq "${CRON_JOB}"; then
        crontab -l | grep -Fv "${CRON_JOB}" | crontab -
    fi

    if [[ -z "$(crontab -l)" ]]; then
        echo "${CRON_JOB}" | crontab -
    else
        (echo "$(crontab -l)"; echo "${CRON_JOB}") | crontab -
    fi
}

function cron_job_sync_push () {
    REMOTE_USER=${1}
    REMOTE_HOST=${2}
    REMOTE_HOME_PATH="${HOME_PATH//${CUR_USER}/${REMOTE_USER}}"
    REMOTE_SCRIPT_PATH="${SCRIPT_PATH//${CUR_USER}/${REMOTE_USER}}"
    REMOTE_DATA_PATH="${REMOTE_HOME_PATH}/data"
    REMOTE_BACKUP_PATH="${REMOTE_HOME_PATH}/backup"
    BACKUP_FILE=$(ls -1 "${BACKUP_PATH}" | tail -n 1)

    function clean_push () {
        cd "${BACKUP_PATH}" || exit
        DELETE_LIST=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "ls -1 '${REMOTE_BACKUP_PATH}' | sort | head -n -${KEEP_CNT}")
        for DELETE_FILE in ${DELETE_LIST}; do
            ssh "${REMOTE_USER}@${REMOTE_HOST}" "rm -f '${REMOTE_BACKUP_PATH}/${DELETE_FILE}'"
        done
        cd -
    }

    function sync_push () {
        scp "${BACKUP_PATH}/${BACKUP_FILE}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BACKUP_PATH}/"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo service ${APP_NAME} stop"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "rm -rf ${REMOTE_DATA_PATH}/*"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_DATA_PATH}/..; tar -zxf ${REMOTE_BACKUP_PATH}/${BACKUP_FILE}"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_SCRIPT_PATH}; git clean -xdf; git checkout .; git pull"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "${REMOTE_SCRIPT_PATH}/${SCRIPT_FILE} restore"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "${REMOTE_SCRIPT_PATH}/${SCRIPT_FILE} deploy"
    }

    clean_push
    sync_push
}

function cron_add_sync_pull () {
    REMOTE_USER=${1}
    REMOTE_HOST=${2}
    CRON_JOB="0 3 * * 1 ${SCRIPT_PATH}/${SCRIPT_FILE} cron job_sync_pull ${REMOTE_USER} ${REMOTE_HOST}"
    if crontab -l 2>/dev/null | grep -Fq "${CRON_JOB}"; then
        crontab -l | grep -Fv "${CRON_JOB}" | crontab -
    fi

    if [[ -z "$(crontab -l)" ]]; then
        echo "${CRON_JOB}" | crontab -
    else
        (echo "$(crontab -l)"; echo "${CRON_JOB}") | crontab -
    fi
}

function cron_job_sync_pull () {
    REMOTE_USER=${1}
    REMOTE_HOST=${2}
    REMOTE_HOME_PATH="${HOME_PATH//${CUR_USER}/${REMOTE_USER}}"
    REMOTE_BACKUP_PATH="${REMOTE_HOME_PATH}/backup"
    REMOTE_BACKUP_FILE=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "ls -1 '${REMOTE_BACKUP_PATH}' | tail -n 1")

    function clean_pull () {
        cd "${BACKUP_PATH}" || exit
        DELETE_LIST=$(ls -1 "${BACKUP_PATH}" | sort | head -n -${KEEP_CNT})
        for DELETE_FILE in ${DELETE_LIST}; do
            rm -f ${BACKUP_PATH}/${DELETE_FILE}
        done
        cd -
    }

    function sync_pull () {
        scp "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BACKUP_PATH}/${REMOTE_BACKUP_FILE}" "${BACKUP_PATH}/"
        sudo service ${APP_NAME} stop
        rm -rf ${DATA_PATH}/*
        cd ${DATA_PATH}/..; tar -zxf ${BACKUP_PATH}/${REMOTE_BACKUP_FILE}
        cd ${SCRIPT_PATH}; git clean -xdf; git checkout .; git pull
        ${SCRIPT_PATH}/${SCRIPT_FILE} restore
        ${SCRIPT_PATH}/${SCRIPT_FILE} deploy
    }

    clean_pull
    sync_pull
}

export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
cd ${SCRIPT_PATH}

if [[ ${OPTION} == 'init' ]]; then
    sudo apt install libgl1 -y
    mkdir -p ${PYTHON_PATH}
    virtualenv ${PYTHON_PATH}
    source ${PYTHON_ENV}
    pip3 install -r ${SCRIPT_PATH}/requirements.txt
    if [[ ${#} -eq 5 ]]; then
        flask init --mail_address ${3} --mail_password ${5}
    else
        echo "${SCRIPT_FILE} init --mail_address EMAIL_ADDRESS --mail_password EMAIL_PASSWORD"
    fi
    exit 0
fi

source ${PYTHON_ENV}

if [[ ${OPTION} == 'debug' ]]; then
    python3 ${EXEC_FILE}
elif [[ ${OPTION} == 'run' ]]; then
    nohup gunicorn -w 1 -b 127.0.0.1:4100 'hallelujah:create_app()' > /dev/null 2>&1 &
elif [[ ${OPTION} == 'clean' ]]; then
    code_clean
elif [[ ${OPTION} == 'test' ]]; then
    flask test
elif [[ ${OPTION} == 'backup' ]]; then
    flask backup
elif [[ ${OPTION} == 'restore' ]]; then
    flask restore
elif [[ ${OPTION} == 'check' ]]; then
    flask check
elif [[ ${OPTION} == 'addusr' ]]; then
    if [[ ${#} -ne 5 ]]; then
        echo "${SCRIPT_FILE} addusr --username USERNAME --password PASSWORD"
        exit -1
    fi
    flask addusr --username ${3} --password ${5}
elif [[ ${OPTION} == 'delusr' ]]; then
    if [[ ${#} -ne 3 ]]; then
        echo "${SCRIPT_FILE} delusr --username"
        exit -1
    fi
    flask delusr --username ${3}
elif [[ ${OPTION} == 'deploy' ]]; then
    sudo cp ${SCRIPT_PATH}/service.conf ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|USER_NAME|${CUR_USER}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|PROJECT_PATH|${SCRIPT_PATH}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|PYTHON_PATH|${PYTHON_PATH}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    sudo sed -i "s|NUM_WORKERS|${NUM_WORKERS}|g" ${SERVICE_PATH}/${SERVICE_NAME}
    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    sudo systemctl restart ${SERVICE_NAME}
elif [[ ${OPTION} == 'cron' ]]; then
    CRON_CMD=${2}
    if [[ ${CRON_CMD} == 'add_backup' ]]; then
        cron_add_backup
    elif [[ ${CRON_CMD} == 'job_backup' ]]; then
        cron_job_backup
    elif [[ ${CRON_CMD} == 'add_sync_pull' && ${#} -eq 4 ]]; then
        cron_add_sync_pull ${3} ${4}
    elif [[ ${CRON_CMD} == 'job_sync_pull' && ${#} -eq 4 ]]; then
        cron_job_sync_pull ${3} ${4}
    elif [[ ${CRON_CMD} == 'add_sync_push' && ${#} -eq 4 ]]; then
        cron_add_sync_push ${3} ${4}
    elif [[ ${CRON_CMD} == 'job_sync_push' && ${#} -eq 4 ]]; then
        cron_job_sync_push ${3} ${4}
    else
        echo "Usage: ${SCRIPT_FILE} cron with command"
        echo "    cron [add_backup|job_backup]"
        echo "    cron [add_sync_pull|job_sync_pull|add_sync_push|job_sync_push] remote_user remote_host"
    fi
else
    echo "Usage: ${SCRIPT_FILE} [init|debug|run|deploy|cron|test|clean|addusr|delusr|backup|restore|check]"
fi

