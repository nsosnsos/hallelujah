## Hallelujah
### Flask project based on python 3.10.6

## Software dependency for deploy
- nginx 1.18.0
- redis-server 6.0.16
- mariadb-server 10.6.12(optional)

## Front-end component dependency
1. jquery@3.6.1
2. bootstrap@5.2.2
3. bootstrap-icons@1.9.1
4. dropzone@6.0.0
5. highlightjs@11.6.0
6. github-markdown-css@5.1.0
7. bootswatch5
8. gridjs
9. simplemde

## Features
1. mark-down article, including code syntax highlight.
2. photo gallery with thumbnail, auto aligned to fit window width.
3. file browser, support file multiple upload by dropping or selecting.
4. favorite hyperlink with categories.
5. redis session support for multiple workers.
6. easy to use by flasky script with command: init|debug|run|deploy|clean|backup|restore.
7. log every view url access with real ip address, and authentication information.

## About
* database suport
  - mysql/mariadb/sqlite

* Usage
  - Initialization, including database creation and add administrator.
  ```shell
  bash flasky.sh init --mail_address EMAIL_ADDRESS --mail_password EMAIL_PASSWORD
  ```
  > You could also manually create, migrate and upgrade database, by using flask migration utility.
  ```shell
  flask db init
  flask db migrate
  flask db upgrade
  ```

  - Debug application.
  ```shell
  bash flasky.sh debug
  ```
  - Run application.
  ```shell
  bash flasky.sh run
  ```
  - Deploy application.
  ```shell
  bash flasky.sh deploy
  ```
  - Test application.
  ```shell
  bash flasky.sh test
  ```
  - Clean on the repository.
  ```shell
  bash flasky.sh clean
  ```
  - Add a user.
  ```shell
  bash flasky.sh addusr --username USERNAME --password PASSWORD --mail_address USERNAME@SERVER.COM
  ```
  - Delete a user.
  ```shell
  bash flasky.sh delusr --username USERNAME
  ```
  - Backup mariadb.
  ```shell
  bash flasky.sh backup
  ```
  - Restore mariadb.
  ```shell
  bash flasky.sh restore
  ```

