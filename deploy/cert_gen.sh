#!/bin/bash

set -e
set -x

if [ "${#}" -eq 1 ]; then
	cert_dir=${1}
	echo "${cert_dir}"
	apt-get install openssl
	openssl req -x509 -newkey rsa:4096 -nodes -out "${cert_dir}"/cert.pem -keyout "${cert_dir}"/key.pem -days 9999 -subj "/C=CN/ST=Shaanxi/L=Xi'an/O=Global Security/OU=IT Department/CN=test@gmail.com"
else
	echo "Error: no cert path specified!"
	exit 1
fi
