import os

import numpy as np
import vision
from PIL import Image
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, BigInteger
from sqlalchemy import ForeignKey, Table, PickleType
from sqlalchemy.orm import relationship, backref
from vision.track.interpolation import LinearFill
from vatic.models import Video
from flask_login.mixins import UserMixin
from vatic.meta_table import video_evaluation_association_table, classifier_evaluation_association_table

from db_util import Base
import config


class User(Base, UserMixin):
    __tablename__   = "users"

    id              = Column(Integer, primary_key = True)
    username            = Column(String(250), index = True)
    password            = Column(String(250))

    # one to many
    videos = relationship(Video)
    # one to many
    classifiers = relationship('Classifier')


    def get_id(self):
        return self.id

    def check_password(self, password):
        return self.password == password


class Classifier(Base):
    __tablename__   = "classifiers"

    id              = Column(Integer, primary_key = True)
    name            = Column(String(250), index = True)

    owner_id = Column(Integer, ForeignKey("users.id"))

    # one to many
    videos = relationship(Video)
    # one to many
    children = relationship("Classifier")

    parent_id = Column(Integer, ForeignKey("classifiers.id"))

    # training images
    training_image_list_file_path  = Column(String(550))
    training_label_list_file_path  = Column(String(550))
    epoch   = Column(Integer, default=0)


    # a string to indicate the network type: ['Fast_RCNN', 'mxnet']
    network_type  = Column(String(250))

    # the name of model, specified by the user
    model_name  = Column(String(250))

    # training status: [(0, none), (1, waiting), (2, training), (3, finished)]
    training_status   = Column(Integer, default=0)
    training_start_time   = Column(BigInteger)
    training_end_time   = Column(BigInteger)

    # many to many
    evaluation_sets = relationship("EvaluationSet", secondary=classifier_evaluation_association_table, back_populates='classifiers')

    container_id   = Column(String(250))


class EvaluationSet(Base):
    __tablename__   = "evaluation_sets"

    id              = Column(Integer, primary_key = True)
    name            = Column(String(250), index = True)

    # many to many
    videos = relationship(Video, secondary=video_evaluation_association_table, back_populates='evaluation_sets')

    classifiers = relationship(Classifier, secondary=classifier_evaluation_association_table, back_populates='evaluation_sets')

    prediction_result_file_path  = Column(String(550))
    roc_graph_file_path  = Column(String(550))
