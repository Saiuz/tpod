host        = "cloudlet015.elijah.cs.cmu.edu"
port        = 5000
localhost   = "{0}:{1}".format(host, port) # your local host
database    = "mysql://vatic:vatic@localhost/vatic" # server://user:pass@localhost/dbname
geolocation = "" # api key for ipinfodb.com
maxobjects = 25
VATIC_URL_PREFIX = '/vatic'
UPLOAD_PATH = 'upload/'
EXTRACT_PATH = 'dataset/extract/'
IMAGE_LIST_PATH = 'dataset/image_list/'
LABEL_LIST_PATH = 'dataset/label_list/'
LABEL_NAME_PATH = 'dataset/label_name/'
# probably no need to mess below this line

import multiprocessing
processes = multiprocessing.cpu_count()

import os.path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

