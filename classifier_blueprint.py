from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file, g, \
    abort, Response
from flask import jsonify
import db_util
import db_helper
from forms import CreateClassifierForm, DeleteClassifierForm, CreateTestClassifierForm
import response_util
import classifier_controller as controller
import json
import config
import time
import random
import util
from flask import send_file

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


@classifier_page.route("/create_train", methods=["POST"])
@login_required
def create_training_classifier():
    form = CreateClassifierForm(request.form)
    if form.validate():
        classifier_name = form.classifier_name.data
        epoch = form.epoch.data
        network_type = form.network_type.data
        video_list = form.video_list.data
        video_list = video_list.split(',')
        print video_list
        label_list = form.label_list.data
        label_list = label_list.split(',')
        print label_list

        controller.create_training_classifier(current_user, classifier_name, epoch, video_list, label_list)

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

                # make the request and send back the file
                ret_file_path = '/tmp/' + str(random.getrandbits(32)) + ".png"
                payload = {
                    'time_remains': 100,
                    'base_classifier_id': base_classifier_id,
                    'format': 'img'
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
