from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file, g, \
    abort, Response
from flask import jsonify
import db_util
from db_util import session
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

classifier_page = Blueprint('classifier_page', __name__, url_prefix='/classifier', template_folder='templates',
                            static_url_path='/static', static_folder='static')


@classifier_page.route("/list", methods=["GET"])
@login_required
def list_classifier():
    return render_template('index_classifier.html', classifiers=db_helper.get_classifiers_of_user(current_user.id))


@classifier_page.route("/available_labels", methods=["POST", "GET"])
@login_required
def available_labels():
    labels = db_helper.get_available_labels()
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
        evaluation = session.query(EvaluationSet).filter(EvaluationSet.id == form.evaluation_id.data).first()
        session.delete(evaluation)
        session.commit()
        session.close()
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

        classifier_name = form.classifier_name.data
        epoch = form.epoch.data
        network_type = form.network_type.data
        video_list = form.video_list.data
        video_list = video_list.split(',')
        print video_list
        label_list = form.label_list.data
        label_list = label_list.split(',')
        label_list = util.get_unique_label_name(label_list)
        print label_list

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
        classifier = session.query(Classifier).filter(Classifier.id == base_classifier_id).first()
        if not classifier:
            session.close()
            return response_util.json_error_response(msg='base classifier not exist')
        session.close()
        epoch = form.epoch.data
        video_list = form.video_list.data
        video_list = video_list.split(',')
        controller.create_iterative_training_classifier(current_user, base_classifier_id, form.classifier_name.data,
                                                        epoch, video_list)

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
        print 'parameter: base classifier %s , long running: %s ' % (str(base_classifier_id), str(long_running))
        if long_running == 'true':
            time_remains = 1000
            if form.time_remains.data:
                time_remains = form.time_remains.data
            if not controller.create_test_classifier(current_user, base_classifier_id, time_remains):
                return response_util.json_error_response(msg='The base classifier not exist')
            else:
                return redirect(request.referrer)
        else:
            host_port = controller.create_short_running_test_classifier(base_classifier_id, 10)
            if not host_port:
                return response_util.json_error_response(msg='The base classifier not exist')
            else:
                # wait for the container to start
                time.sleep(5)
                confidence = 0.61
                if 'confidence' in request.form:
                    confidence = str(request.form['confidence'])
                else:
                    print 'input confidence %s ' % str(confidence)

                # make the request and send back the file
                ret_file_path = '/tmp/' + str(random.getrandbits(32)) + ".png"
                payload = {
                    'time_remains': 10,
                    'base_classifier_id': base_classifier_id,
                    'format': 'img',
                    'confidence': confidence
                }

                url = 'http://localhost:' + str(host_port) + "/detect"
                files = {}
                print 'get files ' + str(request.files)
                for k, v in request.files.items():
                    temp_img_path = '/tmp/' + str(random.getrandbits(32)) + str(v.filename)
                    v.save(temp_img_path)
                    files[k] = open(temp_img_path, 'rb')
                    print 'saved image ' + str(temp_img_path)

                util.get_request_result(url, payload, files, ret_file_path)
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
        classifier = session.query(Classifier).filter(Classifier.id == classifier_id).first()
        if not classifier:
            session.close()
            return response_util.json_error_response(msg='classifier not exist')
        session.close()
        name = form.name.data
        video_list = form.video_list.data
        video_list = video_list.split(',')
        print 'create evaluation with name %s, video list %s ' % (str(name), str(video_list))
        controller.create_evaluation(classifier_id, name, video_list)

        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@classifier_page.route("/push", methods=["POST"])
@login_required
def push_classifier():
    form = PushClassifierForm(request.form)
    if form.validate():
        classifier_id = form.classifier_id.data
        classifier = session.query(Classifier).filter(Classifier.id == classifier_id).first()
        if not classifier:
            session.close()
            return response_util.json_error_response(msg='classifier not exist')
        session.close()
        push_tag_name = 'tpod-image-' + classifier.name + '-' + str(random.getrandbits(32))
        return controller.push_classifier(classifier_id, push_tag_name)

    return response_util.json_error_response(msg=str(form.errors))


