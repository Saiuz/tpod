
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
import os
import shutil
from subprocess import call
import numpy as np
import tpod_models
from vatic.cli import dump
import zipfile


DEFAULT_FOLDER = '/home/suanmiao/workspace/tpod/tmp/'


def parse_args():
    """
    Parse input arguments
    """

    parser = argparse.ArgumentParser(description='Export your label and images into a zip ball')
    parser.add_argument('--video', dest='video',
                        help='The name of the video, notice: it should be the name for that video in TPOD, typically it is organized as userid_videoname', type=str)
    parser.add_argument('--target_folder', dest='target_folder',
                        help='the path for the export folder, it will create a zip ball under that folder',
                        default=DEFAULT_FOLDER, type=str)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    return args


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def export_zip(video_name, target_folder): 
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    else:
        # clear the folder
        shutil.rmtree(target_folder)
        os.makedirs(target_folder)

    cmd = [video_name, "-o", target_folder, "--pascal"]
    import pdb; pdb.set_trace()
    dump(cmd)
    print 'Creating zip ball ...'
    zipf = zipfile.ZipFile(target_folder + '/label_export.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir(target_folder, zipf)
    zipf.close()
    print 'The exported file created, it is under the specified folder, and the name is label_export.zip'


if __name__ == '__main__':
    args = parse_args()
    export_zip(args.video, args.target_folder)


