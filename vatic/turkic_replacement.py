
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

import time
import random
import math
import zipfile
from collections import defaultdict

import cv2
import imagehash
from PIL import Image
from logzero import logger

from models import *
from tpod_models import *
import shutil
from vatic import merge
import velocity
import util
import xml.etree.ElementTree as ET
from vision import ffmpeg
import m_logger
from extensions import db
import dumptools
import db_helper

logger = m_logger.get_logger(os.path.basename(__file__))


def delete_video(video_id):
    session = db.session
    video = session.query(Video).filter(Video.id == video_id).first()
    if video:
        # delete original file
        original_file_path = video.orig_file_path
        if os.path.exists(original_file_path):
            os.remove(original_file_path)

        # delete extract file
        extract_file_path = video.extract_path
        if os.path.exists(extract_file_path):
            shutil.rmtree(extract_file_path)

        # delete labels
        labels = session.query(Label).filter(Label.videoid == video_id).all()
        for label in labels:
            # delete label related path
            paths = session.query(Path).filter(Path.labelid == label.id).all()
            for path in paths:
                session.delete(path)
            session.delete(label)

        # delete segments
        segments = session.query(Segment).filter(Segment.videoid == video_id).all()
        for segment in segments:
            # delete session related job
            jobs = session.query(Job).filter(Job.segmentid == segment.id).all()
            for job in jobs:
                session.delete(job)
            session.delete(segment)
        session.delete(video)
        session.commit()
        return True
    session.commit()
    return False


def constrain_resolution(h, w, max_h, max_w):
    if h <= max_h and w <= max_w:
        target_height, target_width = h, w
    else:
        hw_ratio = float(h) / float(w)
        if hw_ratio > float(max_h) / max_w:
            target_height = max_h
            target_width = target_height / hw_ratio
        else:
            target_width = max_w
            target_height = target_width * hw_ratio
    return int(target_height), int(target_width)


def constrain_image_resolution(image, max_h, max_w):
    h, w, _ = image.shape
    if h <= max_h and w <= max_w:
        return image
        
    hw_ratio = float(h) / float(w)
    if hw_ratio > float(max_h) / max_w:
        target_height = max_h
        target_width = target_height / hw_ratio
    else:
        target_width = max_w
        target_height = target_width * hw_ratio
    image = cv2.resize(image, (int(target_width), int(target_height)))
    return image


def video_to_image_of_resolution(path_video, width, height):
    sequence = ffmpeg.extract(path_video)
    try:
        for frame, image in enumerate(sequence):
            if frame % 100 == 0:
                logger.debug("Decoding frames {0} to {1}"
                    .format(frame, frame + 100))
            image.thumbnail((width, height), Image.BILINEAR)
            path = Video.getframepath(frame, args.output)
            try:
                image.save(path)
            except IOError:
                os.makedirs(os.path.dirname(path))
                image.save(path)
    except:
        print "Aborted. Cleaning up..."
        shutil.rmtree(args.output)
        raise ValueError("Error extracting video")


round_down_to_even = lambda x: int(math.floor(x / 2.) * 2)


def get_resized_video_resolution(path_video):
    # get video resolution information
    cap = cv2.VideoCapture(path_video)
    count = 0
    success, image = cap.read()
    resized_h, resized_w = -1, -1
    if success:
        if len(image.shape) == 3:
            h, w, _ = image.shape
        else:
            h, w = image.shape
        resized_h, resized_w = constrain_resolution(h, w, config.IMAGE_MAX_HEIGHT, config.IMAGE_MAX_WIDTH)
    cap.release()
    # H.264 require the image size to be even
    return round_down_to_even(resized_w), round_down_to_even(resized_h)


def resize_video(path_video, target_width, target_height):
    video_full_name = os.path.basename(path_video)
    video_file_name, ext = os.path.splitext(video_full_name)
    tmp_resized_video_path = '/tmp/{}_{}{}'.format(video_file_name, 'resized', ext)
    ret_code = util.issue_blocking_cmd(config.VIDEO_RESIZE_CMD_PAT.format(path_video, tmp_resized_video_path, target_width, target_height))
    if ret_code != 0:
        raise ValueError("error resizing video")
    return tmp_resized_video_path


def extract_video_to_image(path_video):
    tmp_extracted_video_regex = '/tmp/{}_{}/%d.jpg'.format(os.path.basename(path_video), 'extracted')
    tmp_extracted_video_dir = os.path.dirname(tmp_extracted_video_regex)
    if not os.path.isdir(tmp_extracted_video_dir):
        os.makedirs(tmp_extracted_video_dir)
    ret_code = util.issue_blocking_cmd(config.VIDEO_EXTRACT_CMD_PAT.format(path_video, tmp_extracted_video_regex))
    if ret_code != 0:
        raise ValueError("error extracting video")
    return tmp_extracted_video_dir


def extract(path_video, path_output):
    if not os.path.isdir(path_output):
        os.makedirs(path_output)
    if not os.path.isfile(path_video):
        return False

    target_width, target_height = get_resized_video_resolution(path_video)
    tmp_resized_video_path = resize_video(path_video, target_width, target_height)
    tmp_extracted_video_dir = extract_video_to_image(tmp_resized_video_path)
    # mv to correct location
    idx = 1
    while os.path.exists(os.path.join(tmp_extracted_video_dir, '{}.jpg'.format(idx))):
        tmp_image_path = os.path.join(tmp_extracted_video_dir, '{}.jpg'.format(idx))
        img_path = Video.getframepath(idx-1, path_output)
        if not os.path.isdir(os.path.dirname(img_path)):
            os.makedirs(os.path.dirname(img_path))
        shutil.move(tmp_image_path, img_path)
        logger.debug('moving {} --> {}'.format(tmp_image_path, img_path))
        idx += 1
    return True


def extract_image_sequences(image_path_list, path_output):
    if not os.path.isdir(path_output):
        os.makedirs(path_output)

    count = 0
    for path in image_path_list:
        img_path = Video.getframepath(count, path_output)
        image = cv2.imread(path)
        if image is None:
            continue
        if not os.path.isdir(os.path.dirname(img_path)):
            os.makedirs(os.path.dirname(img_path))
        image = constrain_image_resolution(image, config.IMAGE_MAX_HEIGHT,
                                           config.IMAGE_MAX_WIDTH)
        cv2.imwrite(img_path, image)
        count += 1
    return True


def load(video_name, video_path_output, labels, orig_file_path, user_id, segment_length=2000):
    session = db.session
    # video_name = slug
    # video_path_output = location
    first_frame_path = Video.getframepath(0, video_path_output)
    first_frame = image_exist(first_frame_path)
    if first_frame is None:
        return False
    width = first_frame.shape[1]
    height = first_frame.shape[0]

    # search for last frame
    toplevel = max(int(x)
                   for x in os.listdir(video_path_output))
    secondlevel = max(int(x)
                      for x in os.listdir("{0}/{1}".format(video_path_output, toplevel)))
    maxframes = max(int(os.path.splitext(x)[0])
                    for x in os.listdir("{0}/{1}/{2}"
                                        .format(video_path_output, toplevel, secondlevel))) + 1

    print "Found {0} frames.".format(maxframes)
    last_frame_path = Video.getframepath(maxframes - 1, video_path_output)
    last_frame = image_exist(last_frame_path)
    if last_frame is None:
        return False
    query = session.query(Video).filter(Video.slug == video_name)
    if query.count() > 0:
        print "Video {0} already exists!".format(video_name)
        print "updating labels for {0}".format(video_name)
        # j: add in update label function
        video = session.query(Video).filter(Video.slug == video_name).first()
        # check if such label has any paths associated with it
        for label in video.labels:
            if not session.query(Path).filter(Path.labelid == label.id).count():
                print 'No path associated. deleted label {} {}'.format(label.id, label.text)
                session.delete(label)
            else:
                print 'Path associated exists. keep label {} {}'.format(label.id, label.text)
        existing_labels = [label.text for label in video.labels]
        labelcache = {}
        attributecache = {}
        lastlabel = None
        for labeltext in labels:
            if labeltext[0] == "~":
                if lastlabel is None:
                    print "Cannot assign an attribute without a label!"
                    session.close()
                    return
                labeltext = labeltext[1:]
                attribute = Attribute(text=labeltext)
                session.add(attribute)
                lastlabel.attributes.append(attribute)
                attributecache[labeltext] = attribute
            else:
                if labeltext in existing_labels:
                    print 'label: {} already in video'.format(label)
                    continue
                label = Label(text=labeltext)
                print 'add label: {}'.format(label)
                session.add(label)
                video.labels.append(label)
                labelcache[labeltext] = label
                lastlabel = label
        session.commit()
        return
    homographydir = os.path.abspath(os.path.join("homographies", video_name))
    if not os.path.isdir(homographydir):
        os.makedirs(homographydir)
    np.save(os.path.join(homographydir, "homography.npy"), np.identity(3))

    current_user = session.query(User).filter(User.id == user_id).first()

    # create video
    video = Video(slug=video_name,
                  location=os.path.realpath(video_path_output),
                  width=width,
                  height=height,
                  totalframes=maxframes,
                  skip=0,
                  perobjectbonus=0,
                  completionbonus=0,
                  trainwith=None,
                  isfortraining=False,
                  blowradius=0,
                  homographylocation=homographydir,
                  pointmode=False,
                  orig_file_path=orig_file_path,
                  extract_path=video_path_output,
                  owner_id=user_id)
    session.add(video)
    current_user.videos.append(video)

    print "Binding labels and attributes..."

    # create labels and attributes
    labelcache = {}
    attributecache = {}
    lastlabel = None
    for labeltext in labels:
        if labeltext[0] == "~":
            if lastlabel is None:
                print "Cannot assign an attribute without a label!"
                session.commit()
                return
            labeltext = labeltext[1:]
            attribute = Attribute(text=labeltext)
            session.add(attribute)
            lastlabel.attributes.append(attribute)
            attributecache[labeltext] = attribute
        else:
            label = Label(text=labeltext)
            print 'add label: {}'.format(label)
            session.add(label)
            video.labels.append(label)
            labelcache[labeltext] = label
            lastlabel = label

    print "Creating segments..."
    # create shots and jobs
    startframe = 0
    stopframe = video.totalframes - 1
    for start in range(startframe, stopframe, segment_length):
        stop = min(start + segment_length + 1,
                   stopframe)
        segment = Segment(start=start,
                          stop=stop,
                          video=video)
        job = Job(segment=segment)
        session.add(segment)
        session.add(job)
    session.commit()


def image_exist(img_path):
    try:
        img = cv2.imread(img_path)
        return img
    except Exception:
        print "Image not exist " + str(img_path)
    return None


def publish():
    return None


# ---------- below is code about dump, these two classes are selected from turkic


class Tracklet(object):
    def __init__(self, label, labelid, userid, paths, boxes, velocities):
        self.label = label
        self.paths = paths
        self.boxes = sorted(boxes, key=lambda x: x.frame)
        self.velocities = velocities
        self.labelid = labelid
        self.userid = userid

    def bind(self):
        for path in self.paths:
            self.boxes = Path.bindattributes(path.attributes, self.boxes)


def get_merged_data(video, domerge=True, mergemethod=None, mergethreshold=0.5, groundplane=False):
    response = []
    if domerge:
        for boxes, paths in merge.merge(video.segments,
                                        method=mergemethod,
                                        threshold=mergethreshold,
                                        groundplane=groundplane):
            if (paths[0].label != None):
                tracklet = Tracklet(
                    paths[0].label.text,
                    paths[0].labelid,
                    paths[0].userid,
                    paths,
                    boxes,
                    {}
                )
                response.append(tracklet)
    else:
        for segment in video.segments:
            for job in segment.jobs:
                if not job.useful:
                    continue
                for path in job.paths:
                    tracklet = Tracklet(
                        path.label.text,
                        path.labelid,
                        path.userid,
                        [path],
                        path.getboxes(),
                        {}
                    )
                    response.append(tracklet)

    interpolated = []
    for track in response:
        path = vision.track.interpolation.LinearFill(track.boxes)
        # jj: fix generated flag. the old generated flag only means that frame
        # is linearly interpolated. but in tpod, tracked frame should also
        # be labeled as generated
        # two loops. inefficient...
        for mbx in track.boxes:
            for path_mbx in path:
                if mbx.frame == path_mbx.frame:
                    path_mbx.generated = path_mbx.generated or mbx.generated

        velocities = velocity.velocityforboxes(path)
        tracklet = Tracklet(track.label, track.labelid, track.userid,
                            track.paths, path, velocities)
        interpolated.append(tracklet)
    response = interpolated

    for tracklet in response:
        tracklet.bind()

    return response


# the basic structure: class is separated by '.' label is separated by ';' coordination is separated by ','
def generate_frame_label(frame_labels):
    if len(frame_labels) == 0:
        return '\n'
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


def getdata(video_id):
    video = Video.query.filter(Video.id == video_id)
    if video.count() == 0:
        raise ValueError("Video id ({0}) does not exist!".format(video_id))
    video = video.one()
    groundplane = False
    mergemethod = merge.getpercentoverlap(groundplane)
    merge_threshold = 0.5
    # TODO: doesn't really need to merge the path. change the domerge=False
    return video, get_merged_data(video, True, mergemethod, merge_threshold, False)


def dump_image_and_label_files(video_ids, label_name_array, remove_none_frame=False):
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

    session = db.session

    image_list_array = []
    label_list_array = []
    for video_id in video_ids:
        video, data = getdata(video_id)
        total_frames = video.totalframes
        extract_path = video.extract_path
        # for each video, we create a dict, to store all necessary labels
        # the key is the label name, the value is an array, since there might be multiple boxes for one label
        label_dict = {}
        for track in data:
            print 'get track with name %s, and length %s ' % (str(track.label), str(len(track.boxes)))
            if str(track.label) in label_name_array:
                if str(track.label) not in label_dict:
                    label_dict[str(track.label)] = []
                label_dict[str(track.label)].append(track.boxes)

        # after the traverse, w get all valid labels for that video
        iterators = []
        for label_name in label_name_array:
            if label_name in label_dict:
                iterators.append(label_dict[label_name])
            else:
                iterators.append([])
        # generate labels for each frame
        for frame in range(0, total_frames):
            img_path = Video.getframepath(frame, extract_path)
            if os.path.exists(img_path) and util.is_image_file(img_path):
                image_list_array.append(img_path)
                # traverse through the iterators, to check each label
                current_frame_labels = []
                # each iterator represent the pointer for the array of the class
                for i, iterator in enumerate(iterators):
                    label_boxes = []
                    for j, box_total in enumerate(iterator):
                        if frame >= len(box_total):
                            continue
                        box = box_total[frame]
                        # ignore these lost, occluded, generated labels
                        if box.lost or box.occluded:
                            continue
                        x1 = box.xtl
                        y1 = box.ytl
                        w = (box.xbr - box.xtl)
                        h = (box.ybr - box.ytl)
                        item = [str(x1), str(y1), str(w), str(h)]
                        label_boxes.append(item)
                    current_frame_labels.append(label_boxes)
                # generate the format for that frame of labels
                label_list_array.append(generate_frame_label(current_frame_labels))

    if remove_none_frame:
        filled_image_list_array = []
        filled_label_list_array = []
        for i, frame_item in enumerate(label_list_array):
            # traverse through the frame, if there is no label exist, remove it
            if len(frame_item) >= len(label_name_array):
                # the length should be at least the length of a rect
                filled_image_list_array.append(image_list_array[i])
                filled_label_list_array.append(frame_item)
            else:
                print 'not labeled'
        print 'before remove none labeled array: length: %s, after %s' % (
            str(len(image_list_array)), str(len(filled_image_list_array)))
        image_list_array = filled_image_list_array
        label_list_array = filled_label_list_array

    total_frames = len(image_list_array)
    print 'total length of image %s, length of label %s, total frames %s' % (
        str(len(image_list_array)), str(len(label_list_array)), str(total_frames))
    util.write_list_to_file(image_list_array, image_file_path)
    util.write_list_to_file(label_list_array, label_file_path)

    # create the labels.txt file
    util.write_list_to_file(label_name_array, label_name_path)

    session.commit()
    return image_file_path, label_file_path, label_name_path


def extract_labeled_file(valid_sample_list, path_output):
    if not os.path.isdir(path_output):
        os.makedirs(path_output)

    for i, item in enumerate(valid_sample_list):
        img_path = Video.getframepath(i, path_output)
        origin_img_path = item[1]
        image = cv2.imread(origin_img_path)
        if image is None:
            continue
        if not os.path.isdir(os.path.dirname(img_path)):
            os.makedirs(os.path.dirname(img_path))
        # no resize for labeled image
        cv2.imwrite(img_path, image)


def read_pascal_label(xml_path):
    ret = {}
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find("size")
    height = float(size.find("height").text)
    width = float(size.find("width").text)

    labels = {}
    for label in root.findall('object'):
        object_name = label.find("name").text
        box = label.find("bndbox")
        xmax = float(box.find("xmax").text)
        xmin = float(box.find("xmin").text)
        ymax = float(box.find("ymax").text)
        ymin = float(box.find("ymin").text)
        occlude = False
        temp = box.find("occluded")
        if temp is not None:
            temp = int(temp.text)
            if temp != 0:
                occlude = True
        item = [occlude, xmax, xmin, ymax, ymin]
        if object_name not in labels:
            labels[object_name] = []
        labels[object_name].append(item)
    ret['labels'] = labels
    ret['height'] = height
    ret['width'] = width
    return ret


def load_labeled_sample(video_name, valid_sample_list, video_path_output, orig_file_path, user_id, segment_length=300):
    # video_name = slug
    # video_path_output = location
    first_frame_path = Video.getframepath(0, video_path_output)
    first_frame = image_exist(first_frame_path)
    if first_frame is None:
        return False
    width = first_frame.shape[1]
    height = first_frame.shape[0]

    # load label for all frames
    label_list = []
    labels = []
    for i, item in enumerate(valid_sample_list):
        origin_label_path = item[2]
        frame_label = read_pascal_label(origin_label_path)
        label_list.append(frame_label)
        for label_name, class_labels in frame_label['labels'].iteritems():
            if label_name not in labels:
                labels.append(label_name)

    # search for last frame
    toplevel = max(int(x)
                   for x in os.listdir(video_path_output))
    secondlevel = max(int(x)
                      for x in os.listdir("{0}/{1}".format(video_path_output, toplevel)))
    maxframes = max(int(os.path.splitext(x)[0])
                    for x in os.listdir("{0}/{1}/{2}"
                                        .format(video_path_output, toplevel, secondlevel))) + 1

    print "Found {0} frames.".format(maxframes)
    last_frame_path = Video.getframepath(maxframes - 1, video_path_output)
    last_frame = image_exist(last_frame_path)
    if last_frame is None:
        return False
    query = session.query(Video).filter(Video.slug == video_name)
    if query.count() > 0:
        print "Video {0} already exists!".format(video_name)
        print "updating labels for {0}".format(video_name)
        # j: add in update label function
        video = session.query(Video).filter(Video.slug == video_name).first()
        # check if such label has any paths associated with it
        for label in video.labels:
            if not session.query(Path).filter(Path.labelid == label.id).count():
                print 'No path associated. deleted label {} {}'.format(label.id, label.text)
                session.delete(label)
            else:
                print 'Path associated exists. keep label {} {}'.format(label.id, label.text)
        existing_labels = [label.text for label in video.labels]
        labelcache = {}
        attributecache = {}
        lastlabel = None
        for labeltext in labels:
            if labeltext[0] == "~":
                if lastlabel is None:
                    print "Cannot assign an attribute without a label!"
                    session.close()
                    return
                labeltext = labeltext[1:]
                attribute = Attribute(text=labeltext)
                session.add(attribute)
                lastlabel.attributes.append(attribute)
                attributecache[labeltext] = attribute
            else:
                if labeltext in existing_labels:
                    print 'label: {} already in video'.format(label)
                    continue
                label = Label(text=labeltext)
                print 'add label: {}'.format(label)
                session.add(label)
                video.labels.append(label)
                labelcache[labeltext] = label
                lastlabel = label
        session.commit()
        return
    homographydir = os.path.abspath(os.path.join("homographies", video_name))
    if not os.path.isdir(homographydir):
        os.makedirs(homographydir)
    np.save(os.path.join(homographydir, "homography.npy"), np.identity(3))

    current_user = session.query(User).filter(User.id == user_id).first()

    # create video
    video = Video(slug=video_name,
                  location=os.path.realpath(video_path_output),
                  width=width,
                  height=height,
                  totalframes=maxframes,
                  skip=0,
                  perobjectbonus=0,
                  completionbonus=0,
                  trainwith=None,
                  isfortraining=False,
                  blowradius=0,
                  homographylocation=homographydir,
                  pointmode=False,
                  orig_file_path=orig_file_path,
                  extract_path=video_path_output,
                  owner_id=user_id)
    session.add(video)
    current_user.videos.append(video)

    print "Binding labels and attributes..."

    # create labels and attributes
    labelcache = {}
    attributecache = {}
    lastlabel = None
    for labeltext in labels:
        if labeltext[0] == "~":
            if lastlabel is None:
                print "Cannot assign an attribute without a label!"
                session.commit()
                return
            labeltext = labeltext[1:]
            attribute = Attribute(text=labeltext)
            session.add(attribute)
            lastlabel.attributes.append(attribute)
            attributecache[labeltext] = attribute
        else:
            label = Label(text=labeltext)
            print 'add label: {}'.format(label)
            session.add(label)
            video.labels.append(label)
            labelcache[labeltext] = label
            lastlabel = label

    print "Creating segments..."
    # create shots and jobs
    startframe = 0
    stopframe = video.totalframes - 1
    for start in range(startframe, stopframe, segment_length):
        stop = min(start + segment_length + 1,
                   stopframe)
        segment = Segment(start=start,
                          stop=stop,
                          video=video)
        job = Job(segment=segment)
        session.add(segment)
        session.add(job)

        # traverse through the segment to add path and boxes
        path_array = {}
        for i in range(start, stop + 1):
            frame_label = label_list[i]
            for label_name, class_labels in frame_label['labels'].iteritems():
                # traverse through all boxes/labels under that class
                if label_name not in path_array:
                    path_array[label_name] = []
                while len(path_array[label_name]) < len(class_labels):
                    path = Path()
                    path.label = labelcache[label_name]
                    path.done = 0
                    path.userid = int(user_id)
                    path.job = job
                    path.jobid = job.id
                    session.add(path)
                    session.commit()
                    path_array[label_name].append(path)
                for j, label in enumerate(class_labels):
                    path = path_array[label_name][j]
                    xtl = int(label[2])
                    ytl = int(label[4])
                    xbr = int(label[1])
                    ybr = int(label[3])
                    box = Box(path=path)
                    box.pathid = path.id
                    box.xtl = xtl
                    box.ytl = ytl
                    box.xbr = xbr
                    box.ybr = ybr
                    box.occluded = 0
                    box.outside = 0
                    box.generated = 0
                    box.frame = i
                    session.add(box)
                # for these boxes that disappear in this frame, add a 'out of frame'
                for j in range(len(class_labels), len(path_array[label_name])):
                    path = path_array[label_name][j]
                    box = Box(path=path)
                    box.xtl = 0
                    box.ytl = 0
                    box.xbr = 1
                    box.ybr = 1
                    box.occluded = 0
                    box.outside = 1
                    box.generated = 0
                    box.frame = i
                    session.add(box)
    session.commit()


##############################################
# Export related
##############################################
DEFAULT_FORMAT = "id xtl ytl xbr ybr frame lost occluded generated label attributes"

def create_or_clear_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        shutil.rmtree(directory)
        os.makedirs(directory)

def create_pascal_directory_structure(directory):
    try:
        os.makedirs("{0}/Annotations".format(directory))
    except:
        pass
    try:
        os.makedirs("{0}/ImageSets/Main/".format(directory))
    except:
        pass
    try:
        os.makedirs("{0}/JPEGImages/".format(directory))
    except:
        pass

def zip_and_remove_directory(directory):
    """Zip directory and then remove the dir."""
    zip_file_base_name = '{}_zipped'.format(directory)
    zip_file_path = shutil.make_archive(zip_file_base_name, 'zip', directory)
    logger.debug('The exported file created at {}'.format(zip_file_path))
    shutil.rmtree(directory)
    return zip_file_path

def get_manually_labeled_frame_ids(video):
    """Get manually labled frame ids in the video."""
    _, data = getdata(video.id)
    frame_ids = set()
    for track in data:
        for box in track.boxes:
            if box.lost or box.generated:
                continue
            # found manually labled box
            frame_ids.add(box.frame)
    return sorted(list(frame_ids))

def get_perceptual_hash_different_frame_ids(video,
                                            min_hash_difference_between_key_frames=1):
    """Get the ids of frames whose perceptual hash value are quite different."""
    base_frame_hash = None
    frame_ids = []
    for frame_id in range(video.totalframes):
        img_path = Video.getframepath(frame_id, video.extract_path)
        img = Image.open(img_path)
        img_hash = imagehash.phash(img)
        if base_frame_hash is None or (
                img_hash - base_frame_hash >= min_hash_difference_between_key_frames):
           frame_ids.append(frame_id)
           base_frame_hash = img_hash
        img.close()
    return frame_ids

def get_key_frame_ids(video):
    """Identify key frames in the video.

    Key frames need to satify one of following two criteria:
       1. Manual Labeled frame
       2. Perceptual hash is quite different from previous key frames
    """
    manually_labled_frame_ids = get_manually_labeled_frame_ids(video)
    perceptual_hash_different_frame_ids = get_perceptual_hash_different_frame_ids(video)
    key_frame_ids = set(manually_labled_frame_ids) | set(perceptual_hash_different_frame_ids)
    logger.debug(
        "Key frame selection results: \n {0} of {1} frames are manually labeled \n {2} of {1} have large pHash difference".format(
            len(manually_labled_frame_ids),
            video.totalframes,
            len(perceptual_hash_different_frame_ids)))
    return sorted(list(key_frame_ids))

def filter_data_by_labels(data, restricted_to_labels):
    """Only include tracks whose label is in restricted_to_labels."""
    assert(isinstance(data, list))
    assert(isinstance(restricted_to_labels, list))
    filtered_data = []
    for track in data:
        if track.label not in restricted_to_labels:
            continue
        filtered_data.append(track)
    return filtered_data

def export_videos_pascal(video_ids, target_folder, restricted_to_labels=None,
                         difficultthresh=0, key_frame_only=True,
                         annotated_frame_only=True,
                         eval_percent=0.1):
    create_or_clear_directory(target_folder)
    create_pascal_directory_structure(target_folder)

    for video_id in video_ids:
        video, data = getdata(video_id)
        print "Dumping video {0}".format(video.slug)
        export_video_to_dir_pascal(target_folder, video, data,
                            restricted_to_labels=restricted_to_labels,
                            difficultthresh=difficultthresh,
                            key_frame_only=key_frame_only,
                            annotated_frame_only=annotated_frame_only,
                            eval_percent=eval_percent)
    return zip_and_remove_directory(target_folder)

def export_video_to_dir_pascal(output_dir, video, data, restricted_to_labels,
                        difficultthresh, key_frame_only, annotated_frame_only,
                        eval_percent):
    """Export video in pascal format to a directory.
    restricted_to_labels: a list of labels that need to be exported. If None, then, export all labels.
    difficultthresh: a threshold for determing is an image is 'difficult'. If the annotation box area is smaller
                     than the threshold, then it is difficult.
    key_frame_only: whether to only export frames that are significantly different from previous frames in a video.
                    The similarity of frames are determined by pixel-level perceptual hashing.
    annotated_frame_only: whether to export only frames with annotations. key_frame_only is evaluated first. If 
                          both key_frame_only and this arugment are set to be true, 
                          only annotated key frames are included.
    eval_percent: percentage of frames to include as evaluation set.
    """
    get_strframe = lambda frame: "{}_{}_{}".format(video.id, video.slug, str(frame+1).zfill(10))

    if restricted_to_labels is not None:
        data = filter_data_by_labels(data, restricted_to_labels)

    # find the frame ids to export
    frames_to_export = range(0, video.totalframes)

    # filter by key frames
    if key_frame_only:
        frames_to_export = get_key_frame_ids(video)

    # filter by label names. Export all labels unless user specify a subset
    label_names_in_video = [label_obj['name'] for label_obj in
                            db_helper.get_labels_of_video(video.id)]
    # if users didn't specify a subset of labels, then use
    # all the labels from the video
    if restricted_to_labels is None:
        restricted_to_labels = label_names_in_video
    label_names_to_export = set(label_names_in_video) & set(restricted_to_labels)
    labels_to_export = {
        label_name: set() for label_name in label_names_to_export
    }

    annotation_by_frame = defaultdict(list)
    frames_with_annotation = []
    for track in data:
        for box in track.boxes:
            if box.lost:
                continue
            if box.frame in frames_to_export:
                annotation_by_frame[box.frame].append((box, track))
                frames_with_annotation.append(box.frame)

    # filter by annotation. The frames to be exported need to have annotations for
    # labels to be exported
    if annotated_frame_only:
	frames_to_export = sorted(list(set(frames_with_annotation)))

    logger.debug(
        "Export in pascal format: writing annotations from video {} to {}".format(video, output_dir))

    for frame in frames_to_export:
        boxes = annotation_by_frame[frame]
        strframe = get_strframe(frame)
        filename = "{}/Annotations/{}.xml".format(output_dir, strframe)
        f = open(filename, "w")
        f.write("<annotation>")
        f.write("<folder>JPEGImages</folder>")
        f.write("<filename>{0}.jpg</filename>".format(strframe))

        isempty = True
        for box, track in boxes:
            if box.lost:
                continue

            isempty = False
            labels_to_export[track.label].add(frame)
            difficult = box.area < difficultthresh
            difficult = int(difficult)

            f.write("<object>")
            f.write("<name>{0}</name>".format(track.label))
            f.write("<bndbox>")
            f.write("<xmax>{0}</xmax>".format(box.xbr))
            f.write("<xmin>{0}</xmin>".format(box.xtl))
            f.write("<ymax>{0}</ymax>".format(box.ybr))
            f.write("<ymin>{0}</ymin>".format(box.ytl))
            f.write("</bndbox>")
            f.write("<difficult>{0}</difficult>".format(difficult))
            f.write("<occluded>{0}</occluded>".format(box.occluded))
            f.write("<pose>Unspecified</pose>")
            f.write("<truncated>0</truncated>")
            f.write("</object>")

        f.write("<segmented>0</segmented>")
        f.write("<size>")
        f.write("<depth>3</depth>")
        f.write("<height>{0}</height>".format(video.height))
        f.write("<width>{0}</width>".format(video.width))
        f.write("</size>")
        f.write("<source>")
        f.write("<annotation>{0}</annotation>".format(video.slug))
        f.write("<database>vatic</database>")
        f.write("<image>TPOD</image>")
        f.write("</source>")
        f.write("<owner>")
        f.write("<flickrid>TPOD</flickrid>")
        f.write("<name>TPOD</name>")
        f.write("</owner>")
        f.write("</annotation>")
        f.close()

    logger.debug("{0} of {1} frames are exported".format(len(frames_to_export), video.totalframes))

    logger.debug("Writing image sets...")
    for label, frames in labels_to_export.items():
        filename = "{0}/ImageSets/Main/{1}_trainval.txt".format(output_dir,
                                                                label)
        f = open(filename, "a")
        for frame in frames_to_export:
            f.write(get_strframe(frame))
            f.write(" ")
            if frame in frames:
                f.write("1")
            else:
                f.write("-1")
            f.write("\n")

        f.close()
        train = "{0}/ImageSets/Main/{1}_train.txt".format(output_dir, label)
        shutil.copyfile(filename, train)

    def append_frame_path_to_file(filepath, frame_list, get_strframe_method=get_strframe):
        f = open(filepath, "a")
        if f.tell() > 0 and len(frames_to_export) > 0:
            f.write("\n")
        f.write("\n".join(get_strframe(frame) for frame in frame_list))
        f.close()

    filename = "{0}/ImageSets/Main/trainval.txt".format(output_dir)
    append_frame_path_to_file(filename, frames_to_export)

    filename = "{0}/ImageSets/Main/val.txt".format(output_dir)
    eval_frames_to_export = sorted(random.sample(
        frames_to_export, int(len(frames_to_export) * eval_percent)))
    append_frame_path_to_file(filename, eval_frames_to_export)

    filename = "{0}/ImageSets/Main/train.txt".format(output_dir)
    train_frames_to_export = sorted(list(set(frames_to_export) - set(eval_frames_to_export)))
    append_frame_path_to_file(filename, train_frames_to_export)

    logger.debug("Writing JPEG frames...")
    for frame in frames_to_export:
        strframe = get_strframe(frame)
        path = Video.getframepath(frame, video.extract_path)
        dest = "{0}/JPEGImages/{1}.jpg".format(output_dir, strframe)
        shutil.copyfile(path, dest)

    logger.debug("Done.")

def dump_text(video_id, target_folder):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    video, data = getdata(video_id)

    print "Dumping video {0}".format(video.slug)

    dumpformat = dumptools.DEFAULT_FORMAT.split()
    output_file_path = os.path.join(target_folder, os.path.splitext(video.slug)[0])
    with open(output_file_path, 'wb') as f:
        dumptools.dumptext(f, data, False, dumpformat)
    print "finished"
