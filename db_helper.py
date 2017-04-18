import db_util
from vatic.models import *
from tpod_models import *


def generate_label_obj(label):
    obj = {
        'name':label.text,
        'id':label.id,
        'labeled_frame': get_labeled_frames_count(label)
    }
    return obj


def get_labeled_frames_count(label):
    session = db_util.renew_session()
    frame_label_dict = dict()
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
            item_str = key + ','.join(item)
            frame_label_dict[item_str] = True
    session.close()
    return len(frame_label_dict)


def generate_video_obj(video):
    obj = {
        'name':video.slug,
        'id':video.id,
        'labels': get_labels_of_video(video.id),
        'job_urls': get_all_job_urls(video)
    }
    return obj


def get_all_job_urls(video):
    result = []
    for segment in video.segments:
        for job in segment.jobs:
            obj = {
                'url': job.offlineurl(''),
                'index': len(result)
            }
            result.append(obj)
    return result


def get_labels_of_video(video_id):
    session = db_util.renew_session()
    query_result = session.query(Label).filter(Label.videoid == video_id)
    result = []
    for label in query_result:
        result.append(generate_label_obj(label))
    session.close()
    return result


def get_video_by_id(video_id):
    session = db_util.renew_session()
    query_result = session.query(Video).filter(Video.id == video_id).first()
    if query_result:
        ret = generate_video_obj(query_result)
        session.close()
        return ret
    else:
        session.close()
        return None


def get_videos_of_user(user_id):
    session = db_util.renew_session()
    query_result = session.query(Video).filter(Video.owner_id == user_id).all()
    result = []
    for video in query_result:
        result.append(generate_video_obj(video))
    session.close()
    return result


def get_available_videos(user_id):
    session = db_util.renew_session()
    query_result = session.query(Video).filter(Video.owner_id == user_id).all()
    result = []
    for video in query_result:
        obj = {
            'name':video.slug,
            'id':video.id,
        }
        result.append(obj)
    session.close()
    return result


def get_available_labels():
    session = db_util.renew_session()
    query_result = session.query(Label).all()
    result = []
    for label in query_result:
        video_name = label.video.slug
        obj = {
            'video_name': str(video_name),
            'name': str(label.text),
            'id':label.id,
            'labeled_frame': get_labeled_frames_count(label)
        }
        result.append(obj)
    session.close()
    return result


def get_videos_labels_of_classifier(classifier):
    session = db_util.renew_session()
    videos = []
    for video in classifier.videos:
        video_obj = {
            'name':video.slug,
            'id': video.id,
        }
        videos.append(video_obj)
        # search all labels of that video
    if classifier.labels is not None and len(str(classifier.labels)) > 0:
        labels = str(classifier.labels).split(',')
    else:
        labels = []
    session.close()
    return videos, labels


def get_classifiers_of_user(user_id):
    session = db_util.renew_session()
    query_result = session.query(Classifier).filter(Classifier.owner_id == user_id).all()
    result = []
    for classifier in query_result:
        videos, labels = get_videos_labels_of_classifier(classifier)
        obj = {
            'name':classifier.name,
            'id': classifier.id,
            'videos': videos,
            'labels': labels,
        }

        result.append(obj)
    session.close()
    return result



