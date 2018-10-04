
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

import argparse
import sys
import shutil
import os
import time
from os.path import basename
import zipfile
import shutil
from vatic.models import *
import cv2
import config


def is_image_file(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension.lower() == '.png' or file_extension.lower() == '.jpg' or file_extension.lower() == '.jpeg'


def is_xml(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension.lower() == '.xml'


def add_labeled_file(zip_file_path):
    # unzip the file to the extract path
    zip_ref = zipfile.ZipFile(zip_file_path)
    info_list = zip_ref.infolist()
    # create folder in upload
    timestamp = str(long(time.time()))
    upload_folder = config.UPLOAD_PATH + timestamp + '/'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    path_list = []
    image_map = {} 
    label_map = {} 
    for info in info_list:
        file_name = info.filename
        _, file_extension = os.path.splitext(file_name)
        if is_image_file(file_name):
            file_path = zip_ref.extract(info, path=upload_folder)
            path_list.append(file_path)
        # put the file into
        basic_name = basename(file_name)
        name_no_ext = os.path.splitext(basic_name)[0]
        if is_image_file(basic_name): 
            file_path = zip_ref.extract(info, path=upload_folder)
            image_map[name_no_ext] = file_path
        elif is_xml(basic_name):
            file_path = zip_ref.extract(info, path=upload_folder)
            label_map[name_no_ext] = file_path
            
    # now, all image paths are stored in the path_list
    # then extract these images
    extract_path = config.EXTRACT_PATH + os.path.splitext(basename(zip_file_path))[0]
    logger.debug('extract sequence begin %s' % extract_path)
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)

    valid_sample_list = []
    # first, validate the image-label pair 
    for k, v in label_map.iteritems():
        if k in image_map:
            item = [k, image_map[k], label_map[k]]
            valid_sample_list.append(item)

    def compare(x, y):
        return int(x[0]) - int(y[0])

    valid_sample_list = sorted(valid_sample_list, cmp=compare)
    return valid_sample_list, extract_path


def parse_args():
    """
    Parse input arguments
    """

    parser = argparse.ArgumentParser(description='Import your label and images into the database')
    parser.add_argument('--zip_path', dest='zip_path',
                        help='the path for the labeled zip file', type=str)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    add_labeled_file(args.zip_path, "test")


