import os
import server
from werkzeug.serving import run_simple
import logging
import config

logging.basicConfig(filename='vatic-log.txt', level=logging.INFO)
run_simple(config.host,config.port, server.application, use_reloader=True, static_files={'/':os.path.join(os.path.dirname(__file__), 'public')})
