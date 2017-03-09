from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response

label_page = Blueprint('label_page', __name__, url_prefix='/label')


@label_page.route("/list", methods=["GET"])
@login_required
def list_label():
    return Response('<p>List label</p>')


@label_page.route("/delete", methods=["POST"])
@login_required
def delete_label():
    return Response('<p>Delete label</p>')


@label_page.route("/upload", methods=["POST"])
@login_required
def upload_label():
    return Response('<p>Add label</p>')






