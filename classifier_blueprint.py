from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response

classifier_page = Blueprint('classifier_page', __name__, url_prefix='/classifier')


@classifier_page.route("/list", methods=["GET"])
@login_required
def list_classifier():
    return Response('<p>List classifier</p>')


@classifier_page.route("/delete", methods=["POST"])
@login_required
def delete_classifier():
    return Response('<p>Delete classifier</p>')


@classifier_page.route("/upload", methods=["POST"])
@login_required
def upload_classifier():
    return Response('<p>Add classifier</p>')


