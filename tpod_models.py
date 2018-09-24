
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

import os

from extensions import db
from database import Column, Model, CRUDMixin, SurrogatePK, reference_col, relationship
from flask_login.mixins import UserMixin
from vatic.meta_table import video_evaluation_association_table, classifier_evaluation_association_table, video_classifier_association_table
from vatic.models import Video, Label
import config

class User(UserMixin, Model, CRUDMixin):
    __tablename__   = "users"

    id              = Column(db.Integer, primary_key = True)
    username            = Column(db.String(250), index = True)
    password            = Column(db.String(250))

    # one to many
    videos = relationship('Video', backref='users')
    # one to many
    classifiers = relationship('Classifier', backref='users')

    def get_id(self):
        return self.id

    def check_password(self, password):
        return self.password == password


class Classifier(Model, CRUDMixin):
    __tablename__   = "classifiers"

    id              = Column(db.Integer, primary_key = True)
    name            = Column(db.String(250))

    owner_id = Column(db.Integer, db.ForeignKey("users.id"))

    # many to many
    videos = relationship("Video", secondary=video_classifier_association_table, backref='classifiers')

    # it's stored as string array, since there is no reference need
    labels = Column(db.String(250))
    # one to many
    children = relationship("Classifier")

    parent_id = Column(db.Integer, db.ForeignKey("classifiers.id"))

    # training images
    training_image_list_file_path  = Column(db.String(550))
    training_label_list_file_path  = Column(db.String(550))
    training_label_name_file_path  = Column(db.String(550))
    epoch   = Column(db.Integer, default=0)

    # a string to indicate the network type: ['Fast_RCNN', 'mxnet']
    network_type  = Column(db.String(250))

    # the name of model, specified by the user
    model_name  = Column(db.String(250))

    # training status: [(0, none), (1, waiting), (2, training), (3, finished)]
    task_id   = Column(db.String(250))
    # the type of the task: [train, test]
    task_type   = Column(db.String(250))
    training_status   = Column(db.Integer, default=0)
    training_start_time   = Column(db.BigInteger)
    training_end_time   = Column(db.BigInteger)

    # many to many
    evaluation_sets = relationship("EvaluationSet", secondary=classifier_evaluation_association_table, back_populates='classifiers')

    container_id   = Column(db.String(250))
    image_id   = Column(db.String(250))


class EvaluationSet(Model, CRUDMixin):
    __tablename__   = "evaluation_sets"

    id              = Column(db.Integer, primary_key = True)
    name            = Column(db.String(250), index = True)

    # many to many
    videos = relationship('Video', secondary=video_evaluation_association_table, back_populates='evaluation_sets')

    # classifier_id = Column(Integer, ForeignKey("classifiers.id"))
    classifiers = relationship('Classifier', secondary=classifier_evaluation_association_table, back_populates='evaluation_sets')

    prediction_result_file_path  = Column(db.String(550))
    roc_graph_file_path  = Column(db.String(550))

    @property
    def roc_dir(self):
        return os.path.join(config.IMG_PATH, str(self.id))

    @property
    def eval_dir(self):
        return os.path.join(config.EVALUATION_PATH, str(self.id))
