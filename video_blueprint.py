from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import request, url_for, jsonify, Response
import util
import config
import os
import time

video_page = Blueprint('video_page', __name__, url_prefix='/video', template_folder='templates',
                       static_url_path='/static', static_folder='static')

@video_page.route("/index", methods=["GET"])
@login_required
def index():
    return render_template('index_video.html')


@video_page.route("/list", methods=["GET"])
@login_required
def list_video():
    return render_template('index_video.html')


@video_page.route("/delete", methods=["POST"])
@login_required
def delete_video():
    return Response('<p>Delete video</p>')


@login_required
def upload_video():
    return Response('<p>Add video</p>')


@video_page.route("/upload", methods=["POST"])
def upload():
    if request.method == 'POST':
        # we are expected to save the uploaded file and return some infos about it:
        #                              vvvvvvvvv   this is the name for input type=file
        data_file = request.files['file']
        file_name = data_file.filename
        file_path = save_file(data_file, file_name)
        print file_path
        print util.is_video_file(file_name)
        file_size = util.get_file_size(file_path)
        # providing the thumbnail url is optional
        return jsonify(name=file_name,
                       size=file_size)


def save_file(data_file, file_name):
    if not os.path.exists(config.UPLOAD_PATH):
        os.makedirs(config.UPLOAD_PATH)
    timestamp = str(long(time.time()))
    path = config.UPLOAD_PATH + timestamp + '_' + file_name
    data_file.save(path)
    return path

