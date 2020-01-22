#!/bin/bash

set -e
set -x


svc_name=hallelujah
deploy_dir=/home/${svc_name}

root_dir=$(dirname $(dirname "$(readlink -f $0)"))
cert_dir=${deploy_dir}/cert
cert_gen_sh=${root_dir}/deploy/cert_gen.sh
nginx_conf=${root_dir}/deploy/nginx.conf
req_pkg_txt=${root_dir}/requirements.txt

function usage(){
    echo "Usage: build.sh [deploy|clean]"
    exit -1
}

function cert_fail(){
    echo "Certificates build failed!"
    exit -1
}

if [ "$#" -gt 1 ]; then
    usage
elif [ "$#" -eq 1 ]; then
    if [ "$1" == "deploy" ]; then
        op="deploy"
    elif [ "$1" == "clean" ]; then
        op="clean"
    else
        usage
    fi
else
    op="deploy"
fi


if [ $op == "deploy" ]; then
    pip3 install -r ${req_pkg_txt}

    mkdir -p ${cert_dir}
    cert_file=${cert_dir}/cert.pem
    key_file=${cert_dir}/key.pem
	if [ ! -f ${cert_file} ] || [ ! -f ${key_file} ]; then
	    /bin/sh ${cert_gen_sh} ${cert_dir}
		if [ "$?" -ne 0 ]; then
			cert_fail
		fi
	fi

    cp -rf ${nginx_conf} /etc/nginx/sites-available/${svc_name}
    sed -i -e "s/ssl_cert_path/${cert_file//\//\\/}/g" /etc/nginx/sites-available/${svc_name}
    sed -i -e "s/ssl_key_path/${key_file//\//\\/}/g" /etc/nginx/sites-available/${svc_name}
    ln -sf /etc/nginx/sites-available/${svc_name} /etc/nginx/sites-enabled/${svc_name}
    mkdir -p ${deploy_dir}
    cp -rf ${root_dir}/app ${deploy_dir}/
    cp -rf ${root_dir}/config.py ${deploy_dir}/
    cp -rf ${root_dir}/manager.py ${deploy_dir}/
    cp -rf ${root_dir}/site.conf ${deploy_dir}/
    sed -i -e "s/ssl_cert_path/${cert_file//\//\\/}/g" ${deploy_dir}/site.conf
    sed -i -e "s/ssl_key_path/${key_file//\//\\/}/g" ${deploy_dir}/site.conf
    systemctl daemon-reload
    service nginx restart
    cd ${deploy_dir} && python3 ${deploy_dir}/manager.py runserver
else
    rm -rf ${cert_dir}
    rm -rf /etc/nginx/sites-available/${svc_name} /etc/nginx/sites-enabled/${svc_name}
    rm -rf ${deploy_dir}
    systemctl daemon-reload
    service nginx stop
fi
