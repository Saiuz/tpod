
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

# commands
VIDEO_RESIZE_CMD_PAT = 'avconv -i {0} -s {2}x{3} -an {1}' # input, output, width, height
VIDEO_EXTRACT_CMD_PAT = 'avconv -i {0} -f image2 -r 30 -qscale 2 {1}' # input_video, output_regex (qscale controls the quality of extracted images)
