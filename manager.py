# !/usr/bin/env python
# -*- coding:utf-8 -*-

import unittest
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

from app import create_app, db
from app.models import Role, User, Category, Blog, Gallery, Diary, Comment, Tag, Follow, BlogTags


# Avoid GDK_IS_DISPLAY assertion failure
import matplotlib
matplotlib.use('Agg')

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Role=Role, User=User, Category=Category, Blog=Blog, Gallery=Gallery, Diary=Diary,
                Comment=Comment, Tag=Tag, Follow=Follow, BlogTags=BlogTags)


manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host=app.config['SYS_HOST'], port=app.config['SYS_PORT'],
                                        use_debugger=app.config['DEBUG'], ssl_crt=app.config['SSL_CRT'],
                                        ssl_key=app.config['SSL_KEY']))


@manager.command
def test():
    test_set = unittest.TestLoader().discover('test')
    unittest.TextTestRunner(verbosity=2).run(test_set)


@manager.command
def deploy():
    db.drop_all()
    db.create_all()
    Role.insert_roles()
    user_id = User.insert_admin()
    Category.insert_categories(user_id)
    User.add_self_follows()


if __name__ == '__main__':
    manager.run()
