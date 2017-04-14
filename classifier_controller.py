import config
import os
import time
from vatic.models import Video, Label, Box, Path
import db_util
import util


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
# input: a list of video id
# output: the path of the file for that image list file
def generate_image_and_label_file(video_array, label_name_array):
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

