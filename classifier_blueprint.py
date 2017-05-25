from collections import defaultdict

from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file, g, \
    abort, Response
from flask import jsonify


import db_helper
from forms import *
import response_util
import classifier_controller as controller
import json
import config
import time
import random
import util
from flask import send_file
from vatic import turkic_replacement
import parameters
import util

import m_logger

logger = m_logger.get_logger('CLASSIFIER_BLUEPRINT')

classifier_page = Blueprint('classifier_page', __name__, url_prefix='/classifier', template_folder='templates',
                            static_url_path='/static', static_folder='static')


def sol_jsonify(labels):
    '''
    Convert labels to sol format json
    '''
    ret = []
    for label in labels:
        obj = {
            'type': 'option',
            'label': '%s (%s frames, from video %s)' % (
                label['name'], str(label['labeled_frame']), label['video_name']),
            'value': label['name'],
        }
        ret.append(obj)
    return jsonify(ret)


def tag_jsonify(labels):
    label_info = defaultdict(str)
    for label in labels:
        # init with label name
        label_info[label['name']]=label['name']
    for label in labels:
        # add in vidoe info
        label_info[label['name']]+=' ({} frames from video {})'.format(label['labeled_frame'], label['video_name'])
    return jsonify(label_info)


@classifier_page.route("/list", methods=["GET"])
@login_required
def list_classifier():
    return render_template('index_classifier.html', classifiers=db_helper.get_classifiers_of_user(current_user.id))


@classifier_page.route("/available_labels", methods=["POST", "GET"])
@login_required
def available_labels():
    labels = db_helper.get_available_labels()
    return sol_jsonify(labels)


@classifier_page.route("/available_labels_for_videos", methods=["POST"])
@login_required
def available_labels_for_videos():
    video_ids = request.get_json()
    labels = []
    for video_id in video_ids:
        labels.extend(db_helper.get_labels_of_video(video_id))
    return tag_jsonify(labels)



@classifier_page.route("/get_classifier_status", methods=["POST"])
@login_required
def get_classifier_status():
    classifier_ids = request.form['classifier_ids']
    ret = {}
    if classifier_ids is not None:
        classifier_ids = classifier_ids.split(',')
        for classifier_id in classifier_ids:
            status = controller.get_latest_task_status(classifier_id)
            if status is not None:
                ret[str(classifier_id)] = str(status.body)
    return jsonify(ret)


@classifier_page.route("/available_videos", methods=["POST", "GET"])
@login_required
def available_videos():
    videos = db_helper.get_available_videos(current_user.id)
    ret = []
    for video in videos:
        obj = {
            'type': 'option',
            'label': video['name'],
            'value': video['id'],
        }
        ret.append(obj)
    return jsonify(ret)


@classifier_page.route("/available_evaluation_videos", methods=["POST", "GET"])
@login_required
def available_evaluation_videos():
    videos = db_helper.get_available_evaluation_videos(current_user.id)
    ret = []
    for video in videos:
        obj = {
            'type': 'option',
            'label': video['name'],
            'value': video['id'],
        }
        ret.append(obj)
    return jsonify(ret)


@classifier_page.route("/available_classifier_types", methods=["POST", "GET"])
@login_required
def available_classifier_types():
    ret = []
    ret.append({
        'type': 'option',
        'label': 'Faster-RCNN',
        'value': '1',
    })
    return jsonify(ret)


@classifier_page.route("/delete", methods=["POST"])
@login_required
def delete_classifier():
    form = DeleteClassifierForm(request.form)
    if form.validate():
        controller.delete_classifier(form.classifier_id.data)
        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@classifier_page.route("/delete_evaluation", methods=["POST"])
@login_required
def delete_evaluation():
    form = DeleteEvaluationForm(request.form)
    if form.validate():
        controller.delete_evaluation(form.evaluation_id.data)
        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@classifier_page.route("/create_train", methods=["POST"])
@login_required
def create_training_classifier():
    form = CreateClassifierForm(request.form)
    if form.validate():
        # first, check if GPU is enough
        total_used, total, process_usage = util.get_gpu_info(0)
        current_gpu_memory = float(total) - float(total_used)
        if current_gpu_memory < parameters.MINIMUM_TRAIN_GPU_MEMORY:
            return response_util.json_error_response(
                msg='No enough GPU memory, it requires %s MB, but there is only %s MB' % (
                    str(parameters.MINIMUM_TRAIN_GPU_MEMORY), str(current_gpu_memory)))

        classifier_name = util.safe_docker_image_name(form.classifier_name.data)
        if db_helper.has_classifier_name_of_user(classifier_name, current_user):
            return response_util.json_error_response(msg='duplicate classifier name')

        epoch = form.epoch.data
        network_type = form.network_type.data
        video_list = form.video_list.data
        video_list = video_list.split(',')
        print 'creating training job'
        print 'video ids: {}'.format(video_list)
        label_list = form.label_list.data
        label_list = label_list.split(',')
        label_list = util.get_unique_label_name(label_list)
        print 'labels: {}'.format(label_list)
        
        controller.create_training_classifier(current_user, classifier_name, epoch, video_list, label_list)

        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@classifier_page.route("/create_iterative", methods=["POST"])
@login_required
def create_iterative_classifier():
    form = CreateIterativeClassifierForm(request.form)
    if form.validate():
        # first, check if GPU is enough
        total_used, total, process_usage = util.get_gpu_info(0)
        current_gpu_memory = float(total) - float(total_used)
        if current_gpu_memory < parameters.MINIMUM_TRAIN_GPU_MEMORY:
            return response_util.json_error_response(
                msg='No enough GPU memory, it requires %s MB, but there is only %s MB' % (
                    str(parameters.MINIMUM_TRAIN_GPU_MEMORY), str(current_gpu_memory)))

        # one thing should care about is that for both iterative training and evaluation,
        # the base labels.txt (which stores the name and order for labels) should still be the
        # very original (that from the base classifier), thus the labels list should also be organized in
        # that order
        base_classifier_id = form.base_classifier_id.data
        classifier = Classifier.query.filter(Classifier.id == base_classifier_id).first()
        if not classifier:
            return response_util.json_error_response(msg='base classifier not exist')
        epoch = form.epoch.data
        video_list = form.video_list.data
        video_list = video_list.split(',')
        classifier_name = util.safe_docker_image_name(form.classifier_name.data)
        if db_helper.has_classifier_name_of_user(classifier_name, current_user):
            return response_util.json_error_response(msg='duplicate classifier name')
        controller.create_iterative_training_classifier(current_user, base_classifier_id, classifier_name, epoch, video_list)

        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@classifier_page.route("/create_test", methods=["POST"])
@login_required
def create_test_classifier():
    '''
    : return: the status of test classifier (refresh current classifier page), or redirect to the test api
    '''
    '''
    inside the form, there are several parameters
    1. if long running, if it's long running, then there is no redirect, just open the classifier
    2. if short running, it's just a test, it contains image
    {
        long_running: true,
        base_classifier_id: 1234
        img: {img content},
    }
    '''

    form = CreateTestClassifierForm(request.form)
    if form.validate():
        # first, check if GPU is enough
        total_used, total, process_usage = util.get_gpu_info(0)
        current_gpu_memory = float(total) - float(total_used)
        if current_gpu_memory < parameters.MINIMUM_TEST_GPU_MEMORY:
            return response_util.json_error_response(
                msg='No enough GPU memory, it requires %s MB, but there is only %s MB' % (
                    str(parameters.MINIMUM_TEST_GPU_MEMORY), str(current_gpu_memory)))

        base_classifier_id = form.base_classifier_id.data
        long_running = form.long_running.data
        print 'parameter: base classifier %s , long running: %s ' % (str(base_classifier_id
), str(long_running))
        if long_running == 'true':
            time_remains = 1000
            if form.time_remains.data:
                time_remains = form.time_remains.data
            if not controller.create_test_classifier(current_user, base_classifier_id, time_remains):
                return response_util.json_error_response(msg='The base classifier not exist')
            else:
                return redirect(request.referrer)
        else:
            if len(request.files) > 1:
                logger.warning("onetime test received more than 1 image. only the first image is tested!")
            min_cf = str(request.form['confidence'])
            _, cur_file = request.files.items()[0]
            input_image_path = os.path.join('/tmp',
                                            str(random.getrandbits(32))+str(cur_file.filename))
            cur_file.save(input_image_path)
            logger.debug('saved test file to {}'.format(input_image_path))
            ret_file_path = controller.run_onetime_classifier_test(base_classifier_id,
                                                   input_image_path, min_cf)
            if not ret_file_path:
                response_util.json_error_response(msg="Failed to find the classifier")
            return send_file(ret_file_path)
    return response_util.json_error_response(msg=str(form.errors))


@classifier_page.route("/evaluation_img", methods=["POST", "GET"])
@login_required
def evaluation_img():
    file_path = request.args.get('path')
    return send_file(file_path)


@classifier_page.route("/create_evaluation", methods=["POST"])
@login_required
def create_evaluation():
    form = CreateEvaluationForm(request.form)
    if form.validate():
        # first, check if GPU is enough
        total_used, total, process_usage = util.get_gpu_info(0)
        current_gpu_memory = float(total) - float(total_used)
        if current_gpu_memory < parameters.MINIMUM_EVAL_GPU_MEMORY:
            return response_util.json_error_response(
                msg='No enough GPU memory, it requires %s MB, but there is only %s MB' % (
                    str(parameters.MINIMUM_EVAL_GPU_MEMORY), str(current_gpu_memory)))

        if not os.path.exists(config.EVALUATION_PATH):
            os.makedirs(config.EVALUATION_PATH)
        classifier_id = form.classifier_id.data
        classifier = Classifier.query.filter(Classifier.id == classifier_id).first()
        if not classifier:
            return response_util.json_error_response(msg='classifier not exist')
        name = form.name.data
        video_list = form.video_list.data
        video_list = video_list.split(',')
        print 'create evaluation with name %s, video list %s ' % (str(name), str(video_list))
        controller.create_evaluation(classifier_id, name, video_list)
        flash('Evaluation Job Created. Please refresh the page after a few minutes to see the ROC graph.', 'success')
        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@classifier_page.route("/push", methods=["POST"])
@login_required
def push_classifier():
    form = PushClassifierForm(request.form)
    if form.validate():
        classifier_id = form.classifier_id.data
        classifier = Classifier.query.filter(Classifier.id == classifier_id).first()
        if not classifier:
            return response_util.json_error_response(msg='classifier not exist')
        push_tag_name = 'tpod-image-' + current_user.username + '-' + classifier.name
        msg = controller.push_classifier(classifier, push_tag_name)
        flash(msg)
        return redirect(request.referrer)

    return response_util.json_error_response(msg=str(form.errors))


