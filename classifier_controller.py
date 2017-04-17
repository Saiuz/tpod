import ntpath
import os
import time

import config
import db_util
import util
from tpod_models import Classifier
from vatic.models import Video, Label, Box, Path
from celery_tasks import train_task
import random


def generate_image_and_label_file(video_array, label_name_array):
    # input: a list of video id
    # output: the path of the file for that image list file
    '''
    format for image list:
    [
    path1
    path2
    path3
    ]
    format for label list (corresponding to each line in image list):
    [
    label1, label2
    label1,
    label2,
    label1, label2
    ]
    '''
    if not os.path.exists(config.IMAGE_LIST_PATH):
        os.makedirs(config.IMAGE_LIST_PATH)
    if not os.path.exists(config.LABEL_LIST_PATH):
        os.makedirs(config.LABEL_LIST_PATH)
    if not os.path.exists(config.LABEL_NAME_PATH):
        os.makedirs(config.LABEL_NAME_PATH)

    print 'specified labels ' + str(label_name_array)
    timestamp = str(long(time.time()))
    image_file_path = config.IMAGE_LIST_PATH + timestamp + '.txt'
    label_file_path = config.LABEL_LIST_PATH + timestamp + '.txt'
    label_name_path = config.LABEL_NAME_PATH + timestamp + '.txt'

    # label will be stored in the dict uniquely
    label_index_dict = dict()
    for x in range(0, len(label_name_array)):
        label_name = label_name_array[x]
        label_index_dict[label_name] = len(label_index_dict)
    # generate image list file
    session = db_util.renew_session()
    image_list_array = []
    label_list_array = []
    for video_id in video_array:
        video = session.query(Video).filter(Video.id == video_id).first()
        if video is None:
            continue

        # for every video, there will be a dict to store labels related with that frame
        frame_label_dict = dict()

        # retrieve all labels
        labels = session.query(Label).filter(Label.videoid == video_id).all()
        for label in labels:
            # if the label is in the specified label list
            if label.text not in label_index_dict:
                continue
            label_index = label_index_dict[label.text]
            print 'label in the dict ' + str(label_index)
            print 'label name ' + str(label.text)
            # retrieve label related path
            paths = session.query(Path).filter(Path.labelid == label.id).all()
            for path in paths:
                boxes = session.query(Box).filter(Box.pathid == path.id).all()
                for box in boxes:
                    box_frame = box.frame
                    # insert the box into the map, key is the frame id, value is an array of label
                    # each label is also an array containing 4 elements
                    key = str(box_frame)
                    x1 = box.xtl
                    y1 = box.ytl
                    w = (box.xbr - box.xtl)
                    h = (box.ybr - box.ytl)
                    item = [str(x1), str(y1), str(w), str(h)]
                    if key not in frame_label_dict:
                        frame_label_dict[key] = []
                        # each class of label will be an array
                        for x in range(0, len(label_name_array)):
                            frame_label_dict[key].append([])
                    # if not duplicate, add it to the array
                    if not check_duplicate(frame_label_dict[key][label_index], item):
                        # under this array of that class, there would be many labels
                        frame_label_dict[key][label_index].append(item)
        # then, every label is stored in corresponding frame

        total_frames = video.totalframes
        extract_path = video.extract_path
        for x in range(0, total_frames + 1):
            img_path = Video.getframepath(x, extract_path)
            if os.path.exists(img_path) and util.is_image_file(img_path):
                image_list_array.append(img_path)
                if str(x) in frame_label_dict:
                    label_list_array.append(generate_frame_label(frame_label_dict[str(x)]))
                    # print 'there are %s boxes for frame %s' % (str(len(frame_label_dict[str(x)])), str(x))
                    # print 'the generated label line is %s' % (str(generate_frame_label(frame_label_dict[str(x)])))
                else:
                    label_list_array.append('\n')
            else:
                print 'path not exist %s the index is %s ' % (str(image_file_path), str(x))
    print 'total length of image %s, length of label %s, total frames %s' % (str(len(image_list_array)), str(len(label_list_array)), str(total_frames))
    util.write_list_to_file(image_list_array, image_file_path)
    util.write_list_to_file(label_list_array, label_file_path)

    # create the labels.txt file
    util.write_list_to_file(label_name_array, label_name_path)

    session.close()
    return image_file_path, label_file_path, label_name_path


def check_duplicate(parent_array, new_array):
    if len(parent_array) == 0:
        return False
    unique_array = []
    for item in parent_array:
        item_str = ','.join(item)
        unique_array.append(item_str)
    new_str = ','.join(new_array)
    return new_str in unique_array


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


def create_new_classifier(current_user, classifier_name, epoch, video_list, label_list):
    image_list_file_path, label_list_file_path, label_name_file_path = generate_image_and_label_file(video_list, label_list)
    session = db_util.renew_session()
    classifier = Classifier(name=classifier_name, owner_id=current_user.id)
    # add videos
    classifier.training_image_list_file_path = image_list_file_path
    classifier.training_label_list_file_path = label_list_file_path
    classifier.training_label_name_file_path = label_name_file_path

    classifier.model_name = classifier_name
    classifier.epoch = epoch
    classifier.network_type = config.NETWORK_TYPE_FASTER_RCNN

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

    task_id = launch_training_docker_task(classifier_id, train_set_name, epoch)
    print 'launched the docker with task id %s ' % str(task_id)
    classifier.task_id = task_id
    session.commit()
    session.close()


def launch_training_docker_task(classifier_id, train_set_name, epoch, weights=None):
    if weights is None:
        weights = '/VGG_CNN_M_1024.v2.caffemodel'
    task_id = str(classifier_id) + '-' + str(random.getrandbits(32))
    print 'classifier id %s, train set %s, epoch %s, weight %s ' % (str(classifier_id), str(train_set_name), str(epoch), str(weights))
    train_task.apply_async((classifier_id, train_set_name, epoch, weights), task_id=task_id)
    return task_id

# def get_latest_task_status(classifier_id):
    
  

#    id              = Column(Integer, primary_key = True)
#    name            = Column(String(250))
#    owner_id = Column(Integer, ForeignKey("users.id"))
#    # one to many
#    videos = relationship(Video)
#    # one to many
#    children = relationship("Classifier")
#    parent_id = Column(Integer, ForeignKey("classifiers.id"))
#    # training images
#    training_image_list_file_path  = Column(String(550))
#    training_label_list_file_path  = Column(String(550))
#    training_label_name_file_path  = Column(String(550))
#    epoch   = Column(Integer, default=0)
#    # a string to indicate the network type: ['Fast_RCNN', 'mxnet']
#    network_type  = Column(String(250))
#    # the name of model, specified by the user
#    model_name  = Column(String(250))
#    # training status: [(0, none), (1, waiting), (2, training), (3, finished)]
#    task_id   = Column(String(250))
#    training_status   = Column(Integer, default=0)
#    training_start_time   = Column(BigInteger)
#    training_end_time   = Column(BigInteger)
#    # many to many
#    evaluation_sets = relationship("EvaluationSet", secondary=classifier_evaluation_association_table, back_populates='classifiers')
#    container_id   = Column(String(250))
#    image_id   = Column(String(250))




