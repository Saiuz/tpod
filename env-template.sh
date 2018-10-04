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
export FLASK_APP=$DIR/app.py
export FLASK_DEBUG=1
export DB_USER='tpod'
export DB_PASSWORD='secret'
export DB_NAME='tpod'
export CONTAINER_REGISTRY_URL='registry.cmusatyalab.org/junjuew/container-registry'
export DEFAULT_USER='tpod'
export DEFAULT_USER_PASSWORD='secret'

