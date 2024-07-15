#!/usr/bin/env bash
set -x
set -e

HOME_PATH="$(eval echo ~${SUDO_USER})"
SCRIPT_FILE="$(basename $(readlink -f "${0}"))"
SCRIPT_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
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
        rm -f "${DELETE_FILE}"
        ssh "${BACKUP_USR}@${BACKUP_SERVER}" "rm -f '${DELETE_FILE}'"
    done
    cd -
}

function backup () {
    cd ${SCRIPT_PATH}
    rm ${DB_FILE}
    ./flasky.sh backup
    tar -zcf "${BACKUP_PATH}/${BACKUP_FILE}" "${DATA_PATH}"
    cd -
}

function sync () {
    scp "${BACKUP_PATH}/${BACKUP_FILE}" "${BACKUP_USR}@${BACKUP_SERVER}:${BACKUP_PATH}/"
}

clean
backup
sync

