#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from hallelujah import create_app


app = create_app('development')


if __name__ == '__main__':
    app.run(host=app.config.get('SYS_HOST'), port=app.config.get('SYS_PORT'))

