from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import request, url_for, jsonify, Response
import util
import config
import os
import time
from vatic import turkic_replacement
from tpod_models import *
from os.path import basename
from flask import current_app as app
import m_logger
import db_helper

video_page = Blueprint('video_page', __name__, url_prefix='/video', template_folder='templates',
                       static_url_path='/static', static_folder='static')

logger = m_logger.get_logger('VIDEO_PAGE')

@video_page.route("/index", methods=["GET"])
@login_required
def index():
    return render_template('index_video.html')


@video_page.route("/list", methods=["GET"])
@login_required
def list_video():
    return render_template('index_video.html', videos = db_helper.get_videos())


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
        video_name = request.form['video_name']
        data_file = request.files['file']
        logger.debug('receive video %s with name %s' % (str(data_file), video_name))
        file_name = data_file.filename
        file_path = save_file(data_file, file_name)
        if util.is_video_file(file_name):
            add_video(file_path, video_name)
        file_size = util.get_file_size(file_path)
        # providing the thumbnail url is optional
        return jsonify(name=file_name,
                       size=file_size)


def add_video(video_path, video_name):
    extract_path = config.EXTRACT_PATH + os.path.splitext(basename(video_path))[0]
    logger.debug('extract video begin %s' % extract_path)
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    turkic_replacement.extract(video_path, extract_path)
    logger.debug('extract video end %s' % extract_path)
    # there is no label by default
    turkic_replacement.load(video_name, extract_path, [])


def save_file(data_file, file_name):
    if not os.path.exists(config.UPLOAD_PATH):
        os.makedirs(config.UPLOAD_PATH)
    timestamp = str(long(time.time()))
    path = config.UPLOAD_PATH + timestamp + '_' + file_name
    data_file.save(path)
    return path

