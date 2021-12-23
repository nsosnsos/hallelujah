## hallelujah
flask full function website project
based on python 3.7.3

## deploy
* database init
  - login mysql/mariadb: mysql -u root -p
  - create database: CREATE DATABASE IF NOT EXISTS hallelujah DEFAULT CHARSET utf8 COLLATE utf8_bin;
  - python3 manager.py db init
  - python3 manager.py db migrate -m "init"
  - python3 manager.py db upgrade
  - sudo rm -rf migrations

* deploy
  - python3 manager.py deploy

* run server
  - sudo deploy/build.sh
