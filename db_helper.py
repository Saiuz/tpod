from db_util import session
from vatic.models import *
from tpod_models import *


def generate_label_obj(label):
    obj = {
        'name':label.text,
        'id':label.id,
    }
    return obj


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
    query_result = session.query(Label).filter(Label.videoid == video_id)
    result = []
    for label in query_result:
        result.append(generate_label_obj(label))
    return result


def get_video_by_id(video_id):
    query_result = session.query(Video).filter(Video.id == video_id).first()
    if query_result:
        return generate_video_obj(query_result)


def get_videos_of_user(user_id):
    query_result = session.query(Video).filter(Video.owner_id == user_id).all()
    result = []
    for video in query_result:
        result.append(generate_video_obj(video))
    return result


def get_available_videos(user_id):
    query_result = session.query(Video).filter(Video.owner_id == user_id).all()
    result = []
    for video in query_result:
        obj = {
            'name':video.slug,
            'id':video.id,
        }
        result.append(obj)
    return result


def get_available_labels():
    query_result = session.query(Label).all()
    result = []
    for label in query_result:
        video_name = label.video.slug
        obj = {
            'video_name': str(video_name),
            'name': str(label.text),
            'id':label.id,
        }
        result.append(obj)
    return result


def get_videos_labels_of_classifier(classifier):
    videos = []
    label_map = {}
    for video in classifier.videos:
        video_obj = {
            'name':video.slug,
            'id': video.id,
        }
        videos.append(video_obj)
        # search all labels of that video
        query_result = session.query(Label).filter(Label.videoid == video.id).all()
        for label in query_result:
            label_name = label.text
            if label_name not in label_map:
                label_obj = {
                    'name':label_name,
                    'id': label.id,
                }
                label_map[label_name] = label_obj
    labels = []
    for key in label_map.keys():
        labels.append(label_map[key])
    return videos, labels


def get_classifiers_of_user(user_id):
    query_result = session.query(Classifier).filter(Classifier.owner_id == user_id).all()
    result = []
    for classifier in query_result:
        videos, labels = get_videos_labels_of_classifier(classifier)
        obj = {
            'name':classifier.name,
            'id': classifier.id,
            'videos': videos,
            'labels':labels,
        }

        result.append(obj)
    return result



