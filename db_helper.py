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
                'url':job.offlineurl(''),
                'index':len(result)
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


def get_videos():
    query_result = session.query(Video).all()
    result = []
    for video in query_result:
        result.append(generate_video_obj(video))
    return result



