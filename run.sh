#!/bin/bash -ex
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR
./runcelery.py -A celery_tasks worker --loglevel=info &
env/bin/gunicorn -b 0.0.0.0:10000 app:app --log-level=debug --timeout=10000 
