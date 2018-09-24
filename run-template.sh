#!/bin/bash -ex
#
# Copyright 2018 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR &&
source env.sh &&
. env/bin/activate &&
flask db upgrade &&
./runcelery.py -A celery_tasks worker --loglevel=info &
env/bin/gunicorn -b 0.0.0.0:10000 app:app --log-level=debug --timeout=10000 --workers 2

