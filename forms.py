
# Copyright 2018 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField, IntegerField
from wtforms.validators import DataRequired, EqualTo
from wtforms import ValidationError
from tpod_models import User, Classifier, EvaluationSet
import wtforms.validators
from vatic.models import *


class PushClassifierForm(FlaskForm):
    classifier_id = StringField('classifier_id', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        return True


class CreateEvaluationForm(FlaskForm):
    classifier_id = StringField('classifier_id', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    video_list = StringField('video_list', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        return True


class CreateTestClassifierForm(FlaskForm):
    base_classifier_id = StringField('base_classifier_id', validators=[DataRequired()])
    long_running = StringField('long_running', validators=[DataRequired()])
    time_remains = IntegerField('time_remains')

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        return True


class DeleteEvaluationForm(FlaskForm):
    evaluation_id = StringField('evaluation_id', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        evaluation = EvaluationSet.query.filter(EvaluationSet.id == self.evaluation_id.data).first()
        if not evaluation:
            self.evaluation_id.errors.append('evaluation not exist')
            return False
        return True


class DeleteClassifierForm(FlaskForm):
    classifier_id = StringField('classifier_id', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        classifier = Classifier.query.filter(Classifier.id == self.classifier_id.data).first()
        if not classifier:
            self.classifier_id.errors.append('classifier not exist')
            return False
        return True


class CreateIterativeClassifierForm(FlaskForm):
    base_classifier_id = StringField('base_classifier_id', validators=[DataRequired()])
    classifier_name = StringField('classifier_name', validators=[DataRequired()])
    epoch = IntegerField('epoch', validators=[DataRequired()])
    video_list = StringField('video_list', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        return True


class CreateClassifierForm(FlaskForm):
    classifier_name = StringField('classifier_name', validators=[DataRequired()])
    epoch = IntegerField('epoch', validators=[DataRequired()])
    video_list = StringField('video_list', validators=[DataRequired()])
    label_list = StringField('label_list', validators=[DataRequired()])
    network_type = IntegerField('network_type', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        return True


class ExportVideoForm(FlaskForm):
    video_id = StringField('video_id', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        video = Video.query.filter(Video.id == self.video_id.data).first()
        if not video:
            self.video_id.errors.append('video not exist')
            return False
        return True


class DeleteVideoForm(FlaskForm):
    video_id = StringField('video_id', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        video = Video.query.filter(Video.id == self.video_id.data).first()
        if not video:
            self.video_id.errors.append('video not exist')
            return False
        return True


class DeleteLabelForm(FlaskForm):
    label_id = StringField('label_id', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        label = Label.query.filter(Label.id == self.label_id.data).first()
        if not label:
            self.label_id.errors.append('label not exist')
            return False
        return True


class EditLabelForm(FlaskForm):
    label_id = StringField('label_id', validators=[DataRequired()])
    label_name = StringField('label_name', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        FlaskForm.__init__(self, *args, **kwargs)

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        label = Label.query.filter(Label.id == self.label_id.data).first()
        if not label:
            self.label_id.errors.append('label not exist')
            return False
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
        video = Video.query.filter(Video.id == self.video_id.data).first()
        if not video:
            self.video_id.errors.append('video not exist')
            return False
        label = Label.query.filter(Label.videoid == self.video_id.data, Label.text == self.label_name.data).first()
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
        user = User.query.filter_by(username=self.username.data).first()
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
        return True
