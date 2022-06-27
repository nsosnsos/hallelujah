## hallelujah
### flask website project based on python 3.8.1

## about
* database suport
  - mysql/mariadb/sqlite

* Usage
  - Initialization, including database creation and add administrator, fake user and fake articles.
  ```shell
  bash flasky.sh init
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

