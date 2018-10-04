
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

import ntpath
import os
import time
import shutil

import config
import util
from tpod_models import Classifier, EvaluationSet
from vatic.models import Video, Label, Box, Path
from celery_tasks import train_task, test_task, evaluation_task, push_image_task
import random
from celery_model import TaskStatusRecord
from sqlalchemy import desc
from vatic import turkic_replacement
import docker
from extensions import db
import m_logger

logger = m_logger.get_logger('CLASSIFIER_CONTROLLER')

# the basic structure: class is separated by '.' label is separated by ';' coordination is separated by ','
def generate_frame_label(frame_labels):
    if len(frame_labels) == 0:
        return ''
    else:
        line = ''
        # first, travel through all classes
        for ic, item_class in enumerate(frame_labels):
            # then, travel through labels under that class
            if len(item_class) > 0:
                for il, label in enumerate(item_class):
                    str_label = ','.join(label)
                    line += str_label
                    if il != len(item_class) - 1:
                        line += ';'
            if ic != len(frame_labels) - 1:
                line += '.'
        return line


def delete_classifier(classifier_id):
    '''
    1. db entity
    2. label_list, image_list, label_name
    3. container, image
    '''
    classifier = Classifier.query.filter(Classifier.id == classifier_id).first()
    util.remove_file_if_exist(classifier.training_image_list_file_path)
    util.remove_file_if_exist(classifier.training_label_list_file_path)
    util.remove_file_if_exist(classifier.training_label_name_file_path)
    container_image_name = util.get_classifier_image_name(classifier.name,
                                                          classifier.id)
    client = docker.from_env()
    try:
        client.images.remove(container_image_name, force=True)
    except docker.errors.ImageNotFound as e:
        logger.info('contianer image {} not found'.format(container_image_name))
        logger.info(e)
    classifier.delete()


def delete_evaluation(evaluation_id):
    '''
    2. roc image 
    3. eval pkl file
    1. db entity
    '''
    evaluation = EvaluationSet.query.filter(EvaluationSet.id == evaluation_id).first()
    shutil.rmtree(evaluation.roc_dir,  ignore_errors = True)
    shutil.rmtree(evaluation.eval_dir,  ignore_errors = True)
    evaluation.delete()


def create_training_classifier(current_user, classifier_name, epoch, video_list, label_list):
    image_list_file_path, label_list_file_path, label_name_file_path = turkic_replacement.dump_image_and_label_files(
        video_list, label_list, remove_none_frame=True)
    classifier = Classifier.create(name=classifier_name, owner_id=current_user.id)
    # add videos
    classifier.training_image_list_file_path = image_list_file_path
    classifier.training_label_list_file_path = label_list_file_path
    classifier.training_label_name_file_path = label_name_file_path

    classifier.model_name = classifier_name
    classifier.epoch = epoch
    classifier.network_type = config.NETWORK_TYPE_FASTER_RCNN
    classifier.task_type = config.TASK_TYPE_TRAIN

    # add these labels and videos to the classifier
    for video_id in video_list:
        video = Video.query.filter(Video.id == video_id).first()
        if video:
            classifier.videos.append(video)
    classifier.labels = ','.join(label_list)

    # get id of the classifier
    classifier_id = classifier.id
    print 'generate classifier with id %s ' % str(classifier_id)

    # prepare training
    classifier.training_start_time = int(time.time() * 1000)
    train_set_name = os.path.splitext(ntpath.basename(str(image_list_file_path)))[0]

    base_image_name = config.CONTAINER_BASE_IMAGE_URL

    result_image_name = util.get_classifier_image_name(classifier_name, classifier_id)

    task_id = launch_training_docker_task(base_image_name, result_image_name, classifier_id, train_set_name, epoch)
    print 'launched the docker with task id %s ' % str(task_id)
    classifier.task_id = task_id
    db.session.commit()


def create_iterative_training_classifier(current_user, base_classifier_id, classifier_name, epoch, video_list):

    base_classifier = Classifier.query.filter(Classifier.id == base_classifier_id).first()
    if not base_classifier:
        return None
    label_list = str(base_classifier.labels).split(',')
    print 'create iterative training, labels are %s ' % str(label_list)

    image_list_file_path, label_list_file_path, label_name_file_path = turkic_replacement.dump_image_and_label_files(
        video_list, label_list, remove_none_frame=True)

    classifier = Classifier.create(name=classifier_name, owner_id=current_user.id)
    # add videos
    classifier.training_image_list_file_path = image_list_file_path
    classifier.training_label_list_file_path = label_list_file_path
    classifier.training_label_name_file_path = label_name_file_path

    classifier.parent_id = base_classifier_id

    classifier.model_name = classifier_name
    classifier.epoch = epoch
    classifier.network_type = config.NETWORK_TYPE_FASTER_RCNN
    classifier.task_type = config.TASK_TYPE_TRAIN

    # add these labels and videos to the classifier
    classifier.videos = base_classifier.videos
    for video_id in video_list:
        video = Video.query.filter(Video.id == video_id).first()
        if video:
            classifier.videos.append(video)
    classifier.labels = ','.join(label_list)

    # get id of the classifier
    classifier_id = classifier.id
    print 'generate iterative classifier with id %s ' % str(classifier_id)

    # prepare training
    classifier.training_start_time = int(time.time() * 1000)
    train_set_name = os.path.splitext(ntpath.basename(str(image_list_file_path)))[0]

    base_image_name = util.get_classifier_image_name(base_classifier.name, base_classifier.id)

    result_image_name = util.get_classifier_image_name(classifier_name, classifier_id)
    task_id = launch_training_docker_task(base_image_name, result_image_name, classifier_id, train_set_name, epoch, weights='iterative')
    print 'launched the pretrain docker with task id %s ' % str(task_id)
    classifier.task_id = task_id
    db.session.commit()


def launch_training_docker_task(base_image_name, result_image_name, classifier_id, train_set_name, epoch, weights=None):
    if weights is None:
        weights = '/VGG_CNN_M_1024.v2.caffemodel'
    task_id = str(classifier_id) + '-' + str(random.getrandbits(32))
    print 'classifier id %s, train set %s, epoch %s, weight %s ' % (
        str(classifier_id), str(train_set_name), str(epoch), str(weights))
    dataset_path = util.get_dataset_path()
    train_task.apply_async((base_image_name, result_image_name, dataset_path, classifier_id, train_set_name, epoch, weights), task_id=task_id)
    return task_id


def get_latest_task_status(classifier_id):
    classifier = Classifier.query.filter(Classifier.id == classifier_id).first()
    if classifier is None:
        return None
    classifier_query = TaskStatusRecord.query.filter(TaskStatusRecord.task_id == classifier.task_id).order_by(
        desc(TaskStatusRecord.update_time)).first()
    if classifier_query:
        return classifier_query
    return None


def launch_test_docker_task(classifier_id, base_image_name, time_remains, host_port):
    task_id = str(classifier_id) + '-' + str(random.getrandbits(32))
    print 'launching test docker with task id %s ' % str(task_id)
    test_task.apply_async((classifier_id, base_image_name, time_remains, host_port), task_id=task_id)
    return task_id


def create_test_classifier(current_user, base_classifier_id, time_remains=1000):
    base_classifier = Classifier.query.filter(Classifier.id == base_classifier_id).first()
    if not base_classifier:
        return None

    classifier = Classifier.create(name=base_classifier.name, owner_id=current_user.id)
    # add videos
    classifier.training_image_list_file_path = base_classifier.training_image_list_file_path
    classifier.training_label_list_file_path = base_classifier.training_label_list_file_path
    classifier.training_label_name_file_path = base_classifier.training_label_name_file_path

    classifier.task_type = config.TASK_TYPE_TEST
    classifier.parent_id = base_classifier_id

    classifier.model_name = base_classifier.model_name
    classifier.epoch = base_classifier.epoch
    classifier.network_type = base_classifier.network_type

    # add these labels and videos to the classifier
    classifier.videos = base_classifier.videos
    classifier.labels = base_classifier.labels

    # get id of the classifier
    classifier_id = classifier.id
    print 'generate classifier with id %s ' % str(classifier_id)

    classifier.training_start_time = int(time.time() * 1000)

    host_port = util.get_available_port()
    base_image_name = util.get_classifier_image_name(base_classifier.name, base_classifier.id)

    task_id = launch_test_docker_task(classifier_id, base_image_name, time_remains, host_port)
    print 'launched the test docker with task id %s ' % str(task_id)
    classifier.task_id = task_id
    classifier.image_id = task_id
    classifier.container_id = task_id
    db.session.commit()
    return host_port


def create_short_running_test_classifier(base_classifier_id, time_remains=100):
    base_classifier = Classifier.query.filter(Classifier.id == base_classifier_id).first()
    if not base_classifier:
        return None

    host_port = util.get_available_port()
    base_image_name = util.get_classifier_image_name(base_classifier.name, base_classifier.id)

    fake_classifier_id = 'fake-' + str(base_classifier_id)
    task_id = launch_test_docker_task(fake_classifier_id, base_image_name, time_remains, host_port)
    print 'launched the test docker with task id %s ' % str(task_id)
    return host_port


def run_onetime_classifier_test(base_classifier_id, input_image_path, min_cf):
    base_classifier = Classifier.query.filter(Classifier.id == base_classifier_id).first()
    if not base_classifier:
        return None
    base_image_name = util.get_classifier_image_name(base_classifier.name,
                                                     base_classifier.id)    
    if not util.has_container_image(base_image_name):
        return None
    docker_name = 'onetime_test_classifier_' + base_classifier_id + '_' + str(random.getrandbits(16))
    output_image_path = '{}_output.jpg'.format(input_image_path)
    ret_code = util.issue_blocking_cmd(['nvidia-docker', 'run', '--rm', '-v', '/tmp:/tmp',
                             '--name', docker_name, base_image_name,
                             'tools/tpod_detect_cli.py',
                             '--input_image', input_image_path, 
                             '--min_cf', min_cf,
                             '--output_image', output_image_path])
    if ret_code:
        # something went wrong
        return None
    return output_image_path


def create_evaluation(classifier_id, name, video_list):
    classifier = Classifier.query.filter(Classifier.id == classifier_id).first()
    if not classifier:
        print 'classifier not exist'
        return None
    label_list = classifier.labels.split(',')
    evaluation_set = EvaluationSet(name=name)

    for video_id in video_list:
        video = Video.query.filter(Video.id == video_id).first()
        evaluation_set.videos.append(video)

    classifier.evaluation_sets.append(evaluation_set)
    db.session.add(evaluation_set)
    db.session.commit()
    print 'created evaluation set with name %s id %s ' % (str(name), str(evaluation_set.id))
    evaluation_result_name = str(evaluation_set.id)

    base_image_name = util.get_classifier_image_name(classifier.name, classifier.id)

    # prepare label data
    image_list_file_path, label_list_file_path, label_name_file_path = turkic_replacement.dump_image_and_label_files(
        video_list, label_list, remove_none_frame=True)

    # note: this evaluation set name is the unique name to indicate the file name for the label, video,
    # not the name of the data entity

    dataset_path = util.get_dataset_path()
    eval_path = util.get_eval_path()
    evaluation_set_name = os.path.splitext(ntpath.basename(str(image_list_file_path)))[0]
    evaluation_task.apply_async((dataset_path, eval_path, classifier_id, base_image_name, evaluation_set_name, evaluation_result_name))


def push_classifier(classifier, push_tag_name):
    image_name = util.get_classifier_image_name(classifier.name, classifier.id)
    client = docker.from_env()
    try:
        image = client.images.get(str(image_name))
    except docker.errors.ImageNotFound as e:
        logger.error(e)
        return 'Error: no contaienr image found for Classifier: {}'.format(classifier.name)
    push_image_task.delay(image_name, push_tag_name)
    return 'Success: The image is being pushed to registery. \n You can pull the image with command: docker pull {0}:{1} once is finished. You can go to {0} to check its status'.format(config.CONTAINER_REGISTRY_URL, str(push_tag_name))

