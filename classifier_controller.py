import ntpath
import os
import time

import config
import db_util
import util
from tpod_models import Classifier, EvaluationSet
from vatic.models import Video, Label, Box, Path
from celery_tasks import train_task, test_task, evaluation_task, push_image_task
import random
from celery_model import TaskStatusRecord
from sqlalchemy import desc
from vatic import turkic_replacement
import docker


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
    # several necessary steps:
    '''
    1. db entity
    2. label_list, image_list, label_name
    3. container, image
    '''
    session = db_util.renew_session()
    classifier = session.query(Classifier).filter(Classifier.id == classifier_id).first()
    session.delete(classifier)
    session.commit()
    session.close()


def create_training_classifier(current_user, classifier_name, epoch, video_list, label_list):
    image_list_file_path, label_list_file_path, label_name_file_path = turkic_replacement.dump_image_and_label_files(
        video_list, label_list)
    session = db_util.renew_session()
    classifier = Classifier(name=classifier_name, owner_id=current_user.id)
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
        video = session.query(Video).filter(Video.id == video_id).first()
        if video:
            classifier.videos.append(video)
    classifier.labels = ','.join(label_list)

    session.add(classifier)
    session.flush()

    # get id of the classifier
    classifier_id = classifier.id
    print 'generate classifier with id %s ' % str(classifier_id)

    # prepare training
    classifier.training_start_time = int(time.time() * 1000)
    train_set_name = os.path.splitext(ntpath.basename(str(image_list_file_path)))[0]

    base_image_name = 'faster-rcnn-primitive'
    task_id = launch_training_docker_task(base_image_name, classifier_id, train_set_name, epoch)
    print 'launched the docker with task id %s ' % str(task_id)
    classifier.task_id = task_id
    session.commit()
    session.close()


def create_iterative_training_classifier(current_user, base_classifier_id, classifier_name, epoch, video_list):
    session = db_util.renew_session()

    base_classifier = session.query(Classifier).filter(Classifier.id == base_classifier_id).first()
    if not base_classifier:
        session.close()
        return None
    label_list = str(base_classifier.labels).split(',')
    print 'create iterative training, labels are %s ' % str(label_list)

    image_list_file_path, label_list_file_path, label_name_file_path = turkic_replacement.dump_image_and_label_files(
        video_list, label_list)

    classifier = Classifier(name=classifier_name, owner_id=current_user.id)
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
        video = session.query(Video).filter(Video.id == video_id).first()
        if video:
            classifier.videos.append(video)
    classifier.labels = ','.join(label_list)

    session.add(classifier)
    session.flush()

    # get id of the classifier
    classifier_id = classifier.id
    print 'generate iterative classifier with id %s ' % str(classifier_id)

    # prepare training
    classifier.training_start_time = int(time.time() * 1000)
    train_set_name = os.path.splitext(ntpath.basename(str(image_list_file_path)))[0]

    base_image_name = str(base_classifier.task_id)
    task_id = launch_training_docker_task(base_image_name, classifier_id, train_set_name, epoch, weights='iterative')
    print 'launched the pretrain docker with task id %s ' % str(task_id)
    classifier.task_id = task_id
    session.commit()
    session.close()


def launch_training_docker_task(base_image_name, classifier_id, train_set_name, epoch, weights=None):
    if weights is None:
        weights = '/VGG_CNN_M_1024.v2.caffemodel'
    task_id = str(classifier_id) + '-' + str(random.getrandbits(32))
    print 'classifier id %s, train set %s, epoch %s, weight %s ' % (
        str(classifier_id), str(train_set_name), str(epoch), str(weights))
    train_task.apply_async((base_image_name, classifier_id, train_set_name, epoch, weights), task_id=task_id)
    return task_id


def get_latest_task_status(classifier_id):
    session = db_util.renew_session()
    classifier_query = session.query(TaskStatusRecord).filter(TaskStatusRecord.classifier_id == classifier_id).order_by(
        desc(TaskStatusRecord.update_time)).first()
    session.close()
    if classifier_query:
        return classifier_query
    return None


def launch_test_docker_task(classifier_id, docker_image_id, time_remains, host_port):
    task_id = str(classifier_id) + '-' + str(random.getrandbits(32))
    print 'launching test docker with task id %s ' % str(task_id)
    test_task.apply_async((classifier_id, docker_image_id, time_remains, host_port), task_id=task_id)
    return task_id


def create_test_classifier(current_user, base_classifier_id, time_remains=1000):
    session = db_util.renew_session()

    base_classifier = session.query(Classifier).filter(Classifier.id == base_classifier_id).first()
    if not base_classifier:
        return None

    classifier = Classifier(name=base_classifier.name, owner_id=current_user.id)
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

    session.add(classifier)
    session.flush()

    # get id of the classifier
    classifier_id = classifier.id
    print 'generate classifier with id %s ' % str(classifier_id)

    classifier.training_start_time = int(time.time() * 1000)

    host_port = util.get_available_port()
    docker_image_id = base_classifier.task_id

    task_id = launch_test_docker_task(classifier_id, docker_image_id, time_remains, host_port)
    print 'launched the test docker with task id %s ' % str(task_id)
    classifier.task_id = task_id
    classifier.image_id = task_id
    classifier.container_id = task_id
    session.commit()
    session.close()
    return host_port


def create_short_running_test_classifier(base_classifier_id, time_remains=10):
    session = db_util.renew_session()

    base_classifier = session.query(Classifier).filter(Classifier.id == base_classifier_id).first()
    if not base_classifier:
        session.close()
        return None
    session.close()

    host_port = util.get_available_port()
    docker_image_id = base_classifier.task_id

    fake_classifier_id = 'fake-' + str(base_classifier_id)
    task_id = launch_test_docker_task(fake_classifier_id, docker_image_id, time_remains, host_port)
    print 'launched the test docker with task id %s ' % str(task_id)
    return host_port


def create_evaluation(classifier_id, name, video_list):
    session = db_util.renew_session()

    classifier = session.query(Classifier).filter(Classifier.id == classifier_id).first()
    if not classifier:
        session.close()
        print 'classifier not exist'
        return None
    label_list = classifier.labels.split(',')
    evaluation_set = EvaluationSet(name=name)

    for video_id in video_list:
        video = session.query(Video).filter(Video.id == video_id).first()
        evaluation_set.videos.append(video)

    classifier.evaluation_sets.append(evaluation_set)
    session.add(evaluation_set)
    session.commit()
    print 'created evaluation set with name %s id %s ' % (str(name), str(evaluation_set.id))
    evaluation_result_name = str(evaluation_set.id)

    docker_image_id = classifier.task_id

    # prepare label data
    image_list_file_path, label_list_file_path, label_name_file_path = turkic_replacement.dump_image_and_label_files(
        video_list, label_list)

    # note: this evaluation set name is the unique name to indicate the file name for the label, video,
    # not the name of the data entity
    evaluation_set_name = os.path.splitext(ntpath.basename(str(image_list_file_path)))[0]
    evaluation_task.apply_async((classifier_id, docker_image_id, evaluation_set_name, evaluation_result_name))

    session.close()


def push_classifier(classifier_id, push_tag_name):
    session = db_util.renew_session()

    classifier = session.query(Classifier).filter(Classifier.id == classifier_id).first()
    if not classifier:
        session.close()
        return 'classifier not exist'
    image_name = classifier.task_id
    # image_name = '97-2949905851'
    session.close()
    result = push_image_task.delay(image_name, push_tag_name)
    ret = result.get()
    if not ret:
        return 'Error in pushing the image, see the celery log for detail'
    return 'The image has been pushed, the name for that image is %s ' % str(push_tag_name)

    # client = docker.from_env()
    # image = client.images.get(str(image_name))
    # tag_name = 'registry.cmusatyalab.org/junjuew/container-registry:%s' % str(push_tag_name)
    # image.tag(tag_name)
    # ret = client.images.push(tag_name)
    # print ret



# class TaskStatusRecord(Base):
#     __tablename__   = "task_status_records"
#
#     id              = Column(Integer, primary_key = True)
#     task_id  = Column(String(250))
#     classifier_id  = Column(String(250))
#
#     update_time  = DateTime()
#
#     body = Column(String(5000))
