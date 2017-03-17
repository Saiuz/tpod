import config
import os
import time
from vatic.models import Video
import db_util
import util


# input: a list of video id
# output: the path of the file for that image list file
def generate_image_and_label_file(video_array):
    if not os.path.exists(config.IMAGE_LIST_PATH):
        os.makedirs(config.IMAGE_LIST_PATH)
    if not os.path.exists(config.LABEL_LIST_PATH):
        os.makedirs(config.LABEL_LIST_PATH)

    timestamp = str(long(time.time()))
    image_file_path = config.IMAGE_LIST_PATH + timestamp + '.txt'
    label_file_path = config.IMAGE_LIST_PATH + timestamp + '.txt'

    session = db_util.renew_session()
    image_list_array = []
    for video_id in video_array:
        video = session.query(Video).filter(Video.id == video_id).first()
        if video is None:
            continue

        total_frames = video.totalframes
        extract_path = video.extract_path
        for x in range(0, total_frames):
            img_path = Video.getframepath(x, extract_path)
            if os.path.exists(img_path) and util.is_image_file(img_path):
                image_list_array.append(img_path)
    print image_list_array
    util.write_list_to_file(image_list_array, image_file_path)



    return image_file_path, label_file_path


