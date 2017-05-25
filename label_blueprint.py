from flask import Blueprint, render_template, abort
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response
from vatic.models import *
import response_util
import m_logger
from forms import AddLabelForm, DeleteLabelForm, EditLabelForm
from vatic import turkic_replacement

from extensions import db

label_page = Blueprint('label_page', __name__, url_prefix='/label')
logger = m_logger.get_logger('LABEL_PAGE')


@label_page.route("/delete", methods=["POST"])
@login_required
def delete_label():
    form = DeleteLabelForm(request.form)
    if form.validate():
        label = Label.query.filter(Label.id == form.label_id.data).first()
        video = Video.query.filter(Video.id == label.videoid).first()
        video.labels.remove(label)
        label.delete()
        db.session.commit()
        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@label_page.route("/edit", methods=["POST"])
@login_required
def edit_label():
    form = EditLabelForm(request.form)
    if form.validate():
        label = Label.query.filter(Label.id == form.label_id.data).first()
        label.update(text=form.label_name.data)
        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


@label_page.route("/add", methods=["POST"])
@login_required
def add_label():
    form = AddLabelForm(request.form)
    if form.validate():
        label = Label(text = form.label_name.data, videoid = form.video_id.data)
        video = Video.query.filter(Video.id == form.video_id.data).first()
        video.labels.append(label)
        db.session.add(label)
        db.session.commit()
        turkic_replacement.publish()
        return redirect(request.referrer)
    return response_util.json_error_response(msg=str(form.errors))


