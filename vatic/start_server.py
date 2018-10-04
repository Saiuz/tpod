
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

import os
import server
from werkzeug.serving import run_simple
import logging
import config

logging.basicConfig(filename='vatic-log.txt', level=logging.INFO)
run_simple(config.host,config.port, server.application, use_reloader=True, static_files={'/':os.path.join(os.path.dirname(__file__), 'public')})

