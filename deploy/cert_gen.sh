#!/bin/bash

set -e
set -x

if [ "$#" -eq 1 ]; then
	cert_dir=$1
	echo $cert_dir
	apt-get install openssl
	openssl req -x509 -newkey rsa:4096 -nodes -out ${cert_dir}/cert.pem -keyout ${cert_dir}/key.pem -days 1000 << 'EOF'
CN
Shaanxi
Xi'an
.
.
Stan Lee
test@gmail.com
EOF
else
	echo "Error: no cert path specified!"
	exit -1
fi
