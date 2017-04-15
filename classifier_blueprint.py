from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response
from flask import jsonify
import db_util
import db_helper
from forms import CreateClassifierForm, DeleteClassifierForm
import response_util
import classifier_controller as controller

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
            'type':'option',
            'label': '%s (%s frames, from video %s)' % (label['name'],str(label['labeled_frame']),  label['video_name'] ),
            'value':label['name'],
        }
        ret.append(obj)
    return jsonify(ret)


@classifier_page.route("/available_videos", methods=["POST", "GET"])
@login_required
def available_videos():
    videos = db_helper.get_available_videos(current_user.id)
    ret = []
    for video in videos:
        obj = {
            'type':'option',
            'label':video['name'],
            'value':video['id'],
        }
        ret.append(obj)
    return jsonify(ret)


@classifier_page.route("/available_classifier_types", methods=["POST", "GET"])
@login_required
def available_classifier_types():
    ret = []
    ret.append({
         'type':'option',
         'label':'Faster-RCNN',
         'value':'1',
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


@classifier_page.route("/create", methods=["POST"])
@login_required
def create_classifier():
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

        controller.create_new_classifier(current_user, classifier_name,epoch, video_list, label_list)

        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))



