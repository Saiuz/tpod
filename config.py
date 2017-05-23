maxobjects = 25
VATIC_URL_PREFIX = '/vatic'
UPLOAD_PATH = 'upload/'
EXTRACT_PATH = 'dataset/extract/'
IMAGE_LIST_PATH = 'dataset/image_list/'
LABEL_LIST_PATH = 'dataset/label_list/'
LABEL_NAME_PATH = 'dataset/label_name/'
EVALUATION_PATH = 'eval/'
IMG_PATH = 'public/img/'
# probably no need to mess below this line

NETWORK_TYPE_FASTER_RCNN = 'faster_rcnn'
TASK_TYPE_TRAIN = 'train'
TASK_TYPE_TEST = 'test'
CONTAINER_BASE_IMAGE_URL = 'registry.cmusatyalab.org/junjuew/container-registry:faster-rcnn-primitive'
SHORT_RUNNING_CONTAINER_TIME = 100 # in s
IMAGE_MAX_WIDTH=720
IMAGE_MAX_HEIGHT=480

import os
CONTAINER_REGISTRY_URL = os.environ.get('CONTAINER_REGISTRY_URL', 'registry.cmusatyalab.org/junjuew/container-registry')
