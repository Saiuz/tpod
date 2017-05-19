#! /usr/bin/env python
from app import app
from extensions import tpod_celery

if __name__ == '__main__':
    with app.app_context():
        tpod_celery.start()
