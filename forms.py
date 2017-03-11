from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms.validators import DataRequired, EqualTo
from wtforms import ValidationError
from db_util import session
from tpod_models import User
import wtforms.validators
from vatic.models import *


class DeleteLabelForm(FlaskForm):
    label_id = StringField('label_id', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        label = session.query(Label).filter(Label.id == self.label_id.data).first()
        if not label:
            self.label_id.errors.append('label not exist')
            return False
        session.delete(label)
        return True


class AddLabelForm(FlaskForm):
    video_id = StringField('video_id', validators=[DataRequired()])
    label_name = StringField('label_name', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        video = session.query(Video).filter(Video.id == self.video_id.data).first()
        if not video:
            self.video_id.errors.append('video not exist')
            return False
        label = session.query(Label).filter(Label.videoid == self.video_id.data, Label.text == self.label_name.data).first()
        if label:
            self.label_name.errors.append('label already exist')
            return False
        return True


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        user = session.query(User).filter_by(username=self.username.data).first()
        if user is None or (not user.check_password(self.password.data)):
            self.username.errors.append('Invalid username or password')
            return False
        self.user = user
        return True


class SignupForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', [
        DataRequired(),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('confirm_password')

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        user = session.query(User).filter_by(username=self.username.data).first()
