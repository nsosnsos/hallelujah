#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from hallelujah import create_app


app = create_app()


if __name__ == '__main__':
    app.run(host=app.config['SYS_HOST'], port=app.config['SYS_PORT'], debug=app.config['SYS_DEBUG'])

