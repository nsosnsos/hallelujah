## hallelujah
### flask website project based on python 3.10.6

## dependency
1. jquery@3.6.1
2. bootstrap@5.2.2
3. bootstrap-icons@1.9.1
4. dropzone@6.0.0
5. highlightjs@11.6.0
6. github-markdown-css@5.1.0
7. gridjs
8. simplemde

## features
1. mark-down article, including code syntax highlight.
2. photo gallery with thumbnail, auto aligned to fit window width.
3. file browser, support file multiple upload by dropping or selecting.
4. favorite hyperlink with categories.

## about
* database suport
  - mysql/mariadb/sqlite

* Usage
  - Initialization, including database creation and add administrator, fake user and fake articles.
  ```shell
  bash flasky.sh init --mail_address EMAIL_ADDRESS --mail_password EMAIL_PASSWORD
  ```
  > You could also manually create database, then use flask migration utility.
  ```shell
  flask db init
  flask db migrate
  flask db upgrade
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
  - Backup mariadb.
  ```shell
  bash flasky.sh backup
  ```
  - Recovery mariadb.
  ```shell
  bash flasky.sh recovery
  ```

