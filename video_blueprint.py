import random
from flask import Blueprint, render_template, abort, redirect
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import request, url_for, jsonify, Response, flash
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
import zipfile
import shutil
from forms import DeleteVideoForm, ExportVideoForm
import response_util
import import_label
#import export_label
from flask import send_file
import json

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
    videos = db_helper.get_videos_of_user(current_user.id)
    print 'get %s videos for user %s ' % (str(len(videos)), str(current_user.id))
    return render_template('index_video.html', videos = videos)


@video_page.route("/delete", methods=["POST"])
@login_required
def delete_video():
    form = DeleteVideoForm(request.form)
    if form.validate():
        turkic_replacement.delete_video(form.video_id.data)
        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@video_page.route("/upload", methods=["POST"])
def upload():
    if request.method == 'POST':
        video_name = request.form['video_name']
        video = db_helper.select_video_by_slug_and_owner(video_name, current_user)
        if video:
            logger.debug('duplicate video name {}'.format(video_name))
            return jsonify(name=video_name, error='Duplicate file name is not allowed')

        labeled = False
        if 'labeled' in request.form:
            labeled = True
        data_file = request.files['file']
        logger.debug('receive video %s with name %s' % (str(data_file), video_name))
        file_name = data_file.filename
        file_path = save_file(data_file, file_name)
        if util.is_video_file(file_name):
            print 'This is an original video, begin extracting'
            try:
                add_video(file_path, video_name)
                file_size = util.get_file_size(file_path)
                return jsonify(name=file_name,
                       size=file_size)
            except ValueError as e:
                return jsonify(name=file_name, error='video extraction failed')
        elif util.is_zip_file(file_name):
            if not labeled:
                print 'This is an image sequence, begin extracting'
                add_image_sequence(file_path, video_name)
                return jsonify(name=file_name)
            else:
                print 'This is an labeled zip ball, begin extracting'
                ret = add_labeled_zip(video_name, file_path)
                if not ret:
                    # no valid sample pair found, consider it as a image sequence
                    print 'Actually you are fooled, this is an image sequence, begin extracting'
                    add_image_sequence(file_path, video_name)
                return jsonify(name=file_name)
        else:
            return jsonify(name=file_name, error='invalid file type')


def add_video(video_path, video_name):
    extract_path = config.EXTRACT_PATH + os.path.splitext(basename(video_path))[0]
    logger.debug('extract video begin %s' % extract_path)
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    turkic_replacement.extract(video_path, extract_path)
    logger.debug('extract video end %s' % extract_path)
    # there is no label by default
    turkic_replacement.load(video_name, extract_path, [], video_path, current_user.id)


def add_image_sequence(zip_file_path, video_name):
    # unzip the file to the extract path
    zip_ref = zipfile.ZipFile(zip_file_path)
    info_list = zip_ref.infolist()
    # create folder in upload
    timestamp = str(long(time.time()))
    upload_folder = config.UPLOAD_PATH + timestamp + '/'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    path_list = []
    for info in info_list:
        file_name = info.filename
        _, file_extension = os.path.splitext(file_name)
        if util.is_image_file(file_name):
            file_path = zip_ref.extract(info, path=upload_folder)
            path_list.append(file_path)

    # now, all image paths are stored in the path_list
    # then extract these images
    extract_path = config.EXTRACT_PATH + os.path.splitext(basename(zip_file_path))[0]
    logger.debug('extract sequence begin %s' % extract_path)
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    turkic_replacement.extract_image_sequences(path_list, extract_path)
    logger.debug('extract video end %s' % extract_path)
    # delete the temporary unzip path
    shutil.rmtree(upload_folder)
    # there is no label by default
    turkic_replacement.load(video_name, extract_path, [], zip_file_path, current_user.id)


def save_file(data_file, file_name):
    if not os.path.exists(config.UPLOAD_PATH):
        os.makedirs(config.UPLOAD_PATH)
    timestamp = str(long(time.time()))
    path = config.UPLOAD_PATH + timestamp + '_' + file_name
    data_file.save(path)
    return path


def add_labeled_zip(video_name, zip_file_path):
    valid_sample_list, extract_path = import_label.add_labeled_file(zip_file_path)
    if len(valid_sample_list) == 0:
        return False
    turkic_replacement.extract_labeled_file(valid_sample_list, extract_path)
    turkic_replacement.load_labeled_sample(video_name, valid_sample_list, extract_path, zip_file_path, current_user.id)
    return True


def export_zip(video_name, target_folder): 
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    else:
        # clear the folder
        shutil.rmtree(target_folder)
        os.makedirs(target_folder)

    cmd = [video_name, "-o", target_folder, "--pascal"]
    dump(cmd)
    print 'Creating zip ball ...'
    zipf = zipfile.ZipFile(target_folder + '/label_export.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir(target_folder, zipf)
    zipf.close()
    print 'The exported file created, it is under the specified folder, and the name is label_export.zip'


@video_page.route("/export", methods=["GET"])
@login_required
def export():
    if request.args.get('video_id', None):
        video_id = request.args.get('video_id')
        video = Video.query.filter(Video.id == video_id).first()
        if video is None:
            flash('No such video found.', 'danger')
            return redirect(request.referrer)
        target_folder = os.path.join('/tmp', '{}_{}'.format('export', str(random.getrandbits(32))))
        output_file_path = turkic_replacement.dump_pascal(video_id, target_folder)
        if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
            return send_file(output_file_path, as_attachment=True, attachment_filename='export_{}.zip'.format(os.path.splitext(video.slug)[0]))
        else:
            flash('Something went wrong when exporting labels.', 'danger')
            return redirect(request.referrer)
    flash('No such video found.', 'danger')
    return redirect(request.referrer)


# added backdoor for dumping all videos
@video_page.route("/export_text", methods=["GET"])
@login_required
def export_all_text():
    videos_info = db_helper.get_videos_of_user(current_user.id)
    print 'get %s videos for user %s ' % (str(len(videos_info)), str(current_user.id))
    for video_info in videos_info:
        video_id = video_info['id']
        video = Video.query.filter(Video.id == video_id).first()
        if video is None:
            raise ValueError('Video not found :{}'.format(video.id))
        target_folder = os.path.join('/tmp', 'export_test')
        turkic_replacement.dump_text(video_id, target_folder)
    return json.dump('success')

# added backdoor for dumping all videos in pascal
@video_page.route("/export_pascal", methods=["GET"])
@login_required
def export_all_pascal():
    video_infos = db_helper.get_videos_of_user(current_user.id)
    logger.debug('get %s videos for user %s ' % (str(len(video_infos)), str(current_user.id)))
    video_ids = [video_info['id'] for video_info in video_infos]
    target_folder = os.path.join('/tmp', '{}_{}'.format('export', str(random.getrandbits(32))))
    restricted_to_labels = ['tray', 'lever', 'cap', 'dangle', 'assembled', 'clamped']
    output_file_path = turkic_replacement.dump_pascal_multiple_videos(video_ids, target_folder, restricted_to_labels=restricted_to_labels)

    if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
        return send_file(output_file_path, as_attachment=True, attachment_filename='export_{}.zip'.format(os.path.splitext(current_user.username)[0]))
    else:
        return json.dump('Something went wrong when exporting labels.')

# added backdoor for dumping some videos
@video_page.route("/export_some", methods=["GET"])
@login_required
def export_some():
    video_keywords = ["all"]
    video_infos = db_helper.get_videos_of_user(current_user.id)
    video_ids = [video_info['id'] for video_info in video_infos if
                 any([video_keyword in video_info['name'] for video_keyword in video_keywords])]
    logger.debug('exporting video_ids: {}'.format(video_ids))
    target_folder = os.path.join('/tmp', '{}_{}'.format('export', str(random.getrandbits(32))))
    output_file_path = turkic_replacement.dump_pascal_multiple_videos(video_ids, target_folder)

    if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
        return send_file(output_file_path, as_attachment=True, attachment_filename='export_{}.zip'.format(os.path.splitext(current_user.username)[0]))
    else:
        return json.dump('Something went wrong when exporting labels.')
