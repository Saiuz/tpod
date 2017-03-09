from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response

video_page = Blueprint('video_page', __name__, url_prefix='/video')


@video_page.route("/list", methods=["GET"])
@login_required
def list_video():
    return Response('<p>List video</p>')


@video_page.route("/delete", methods=["POST"])
@login_required
def delete_video():
    return Response('<p>Delete video</p>')


@video_page.route("/upload", methods=["POST"])
@login_required
def upload_video():
    return Response('<p>Add video</p>')





