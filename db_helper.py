import db_util
from db_util import session
from vatic.models import *
from tpod_models import *
import config
import os, fnmatch
import re
import cPickle
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def generate_label_obj(label):
    obj = {
        'name': label.text,
        'id': label.id,
        'labeled_frame': get_labeled_frames_count(label)
    }
    return obj


def get_labeled_frames_count(label):
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
    session.commit()
    return len(frame_label_dict)


def generate_video_obj(video):
    obj = {
        'name': video.slug,
        'id': video.id,
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
    session.commit()
    return result


def get_video_by_id(video_id):
    query_result = session.query(Video).filter(Video.id == video_id).first()
    if query_result:
        ret = generate_video_obj(query_result)
        return ret
    else:
        return None


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
            'name': video.slug,
            'id': video.id,
        }
        result.append(obj)
    return result


def get_available_evaluation_videos(user_id):
    query_result = session.query(Video).filter(Video.owner_id == user_id).all()
    result = []
    for video in query_result:
        labels = get_labels_of_video(video.id)
        if len(labels) == 0:
            continue
        total_labeled_frame_count = 0
        for label in labels:
            if 'labeled_frame' in label:
                total_labeled_frame_count += int(label['labeled_frame'])
        if total_labeled_frame_count == 0:
            continue
        obj = {
            'name': video.slug,
            'id': video.id,
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
            'id': label.id,
            'labeled_frame': get_labeled_frames_count(label)
        }
        result.append(obj)
    return result


def get_videos_labels_of_classifier(classifier):
    videos = []
    for video in classifier.videos:
        video_obj = {
            'name': video.slug,
            'id': video.id,
        }
        videos.append(video_obj)
        # search all labels of that video
    if classifier.labels is not None and len(str(classifier.labels)) > 0:
        labels = str(classifier.labels).split(',')
    else:
        labels = []
    return videos, labels


def get_evaluations_of_classifier(classifier):
    matplotlib.use('Agg')
    ret = []
    for evaluation in classifier.evaluation_sets:
        eval_obj = {
            'name': evaluation.name,
            'id': evaluation.id,
            'images': [],
            'videos': [],
        }
        for video in evaluation.videos:
            eval_obj['videos'].append(str(video.slug))
        # read evaluation result if necessary
        evaluation_result_path = config.EVALUATION_PATH + str(evaluation.id)
        if os.path.exists(evaluation_result_path):
            candidate_result = fnmatch.filter(os.listdir(evaluation_result_path), '*.pkl')
            for candidate in candidate_result:
                object_name = os.path.splitext(os.path.basename(candidate))[0]
                object_result = cPickle.load(open(evaluation_result_path + '/' + str(candidate), 'r'))
                rec = object_result['rec']
                prec = object_result['prec']
                ap = object_result['ap']
                print 'read evaluation result, prec %s, ap %s  ' % (str(prec.shape), str(ap))
                fig = plt.figure()
                plt.title('Precision, AP: %s ' % str(ap))
                plt.ylabel('Precision')
                plt.xlabel('Recall')
                ax = fig.add_subplot(111)
                ax.plot(rec, prec)
                img_path = config.IMG_PATH + str(evaluation.id) + '/'
                if not os.path.exists(img_path):
                    os.makedirs(img_path)
                img_path += str(object_name) + '.png'
                plt.savefig(img_path)
                img_obj = {
                    'name':object_name,
                    'path': img_path
                }
                eval_obj['images'].append(img_obj)
        ret.append(eval_obj)
    return ret


def get_classifiers_of_user(user_id):
    query_result = session.query(Classifier).filter(Classifier.owner_id == user_id).all()
    result = []
    for classifier in query_result:
        videos, labels = get_videos_labels_of_classifier(classifier)
        evaluation_sets = get_evaluations_of_classifier(classifier)
        print 'get evaluation %s ' % str(evaluation_sets)
        obj = {
            'name': classifier.name,
            'id': classifier.id,
            'videos': videos,
            'labels': labels,
            'task_type': classifier.task_type,
            'parent_id': classifier.parent_id,
            'evaluation_sets': evaluation_sets
        }
        print 'get task type %s' % str(classifier.task_type)

        result.append(obj)
    return result
