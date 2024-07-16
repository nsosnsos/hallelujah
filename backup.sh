#!/usr/bin/env bash
#set -x
#set -e

HOME_PATH="$(eval echo ~${SUDO_USER})"
SCRIPT_FILE="$(basename $(readlink -f "${0}"))"
SCRIPT_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
WORK_PATH=${HOME_PATH}/workspace
SERVICE_NAME=hallelujah
SERVICE_SCRIPT=flasky.sh
DATA_PATH="${HOME_PATH}/data"
DB_FILE="${DATA_PATH}/hallelujah.sql"
BACKUP_PATH="${HOME_PATH}/backup"
BACKUP_FILE="data_$(date +"%Y%m%d_%H%M%S").tar.gz"
KEEP_CNT=2
BACKUP_USER=ubuntu
BACKUP_SERVER=127.0.0.1


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
    ${SCRIPT_PATH}/flasky.sh backup
    cd ${DATA_PATH}/..
    tar -zcf "${BACKUP_PATH}/${BACKUP_FILE}" "$(basename ${DATA_PATH})"
    cd -
}

function sync () {
    scp "${BACKUP_PATH}/${BACKUP_FILE}" "${BACKUP_USR}@${BACKUP_SERVER}:${BACKUP_PATH}/"
    ssh "${BACKUP_USER}@${BACKUP_SERVER}" "sudo service ${SERVICE_NAME} stop"
    ssh "${BACKUP_USER}@${BACKUP_SERVER}" "rm -rf ${DATA_PATH}/*"
    ssh "${BACKUP_USER}@${BACKUP_SERVER}" "cd ${DATA_PATH}/..; tar -zxf ${BACKUP_PATH}/${BACKUP_FILE}"
    ssh "${BACKUP_USER}@${BACKUP_SERVER}" "${SCRIPT_PATH}/${SERVICE_SCRIPT} restore"
    ssh "${BACKUP_USER}@${BACKUP_SERVER}" "cd ${WORK_PATH}/${SERVICE_NAME}; git clean -xdf; git checkout .; git pull"
    ssh "${BACKUP_USER}@${BACKUP_SERVER}" "sudo service ${SERVICE_NAME} start"
}

clean
backup
sync

