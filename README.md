## Hallelujah
### Flask project based on python 3.10.6

## Software dependency for deploy
- nginx 1.18.0
- redis-server 6.0.16
- mariadb-server 10.6.12(optional, mysql/sqlite are also supported)

## Front-end component dependency
1. jquery@3.7.1
2. bootstrap@5.3.2
3. bootswatch@5.3.2
4. bootstrap-icons@1.11.1
5. dropzone@6.0.0-beta.2
6. highlightjs@11.9.0
7. github-markdown-css@5.3.0
8. clipboard@2.0.11
9. gridjs
10. simplemde

## Features
1. mark-down article, including code syntax highlight.
2. photo gallery with thumbnail, auto aligned to fit window width.
3. file browser, support file multiple upload by dropping or selecting.
4. favorite hyperlink with categories.
5. redis session support for multiple workers.
6. easy to use by flasky script with command: init|debug|run|deploy|cron|test|clean|addusr|delusr|backup|restore.
7. log every view url access with real ip address, and authentication information.
8. simple proxy browser without security check.

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
  - Add cron job for backup and synchronization.
  ```shell
  bash flasky.sh cron
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
  - Backup database.
  ```shell
  bash flasky.sh backup
  ```
  - Restore database.
  ```shell
  bash flasky.sh restore
  ```

