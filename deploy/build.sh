#!/bin/bash

set -e
set -x


svc_name=hallelujah
deploy_dir=/root/${svc_name}

root_dir=$(dirname $(dirname "$(readlink -f $0)"))
cert_dir=/etc/nginx/cert
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
	/bin/sh ${cert_gen_sh} ${cert_dir}
	if [ "$?" -ne 0 ]; then
		cert_fail
	fi
	mkdir -p ${deploy_dir}
	mkdir -p ${cert_dir}
	cp -rf ${nginx_conf} /etc/nginx/sites-available/${svc_name}
	ln -s /etc/nginx/sites-available/${svc_name} /etc/nginx/sites-enabled/${svc_name}
	cp -rf ${root_dir}/* ${deploy_dir}/
	pip3 install -r ${req_pkg_txt}
	service nginx restart
else
	rm -rf ${cert_dir}
	rm -rf /etc/nginx/sites-available/${svc_name} /etc/nginx/sites-enabled/${svc_name}
	rm -rf ${deploy_dir}
	service nginx restart
fi
