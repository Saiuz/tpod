import os

import numpy as np
import vision
from PIL import Image
from sqlalchemy import Column, Integer, Float, String, Boolean
from sqlalchemy import ForeignKey, Table, PickleType
from sqlalchemy.orm import relationship, backref
from vision.track.interpolation import LinearFill
from vatic.models import Video
from flask_login.mixins import UserMixin

from db_util import Base
import config

class User(Base, UserMixin):
    __tablename__   = "user"

    id              = Column(Integer, primary_key = True)
    username            = Column(String(250), index = True)
    password            = Column(String(250))

    video = relationship("Video")
    classifier = relationship("Classifier")


    def get_id(self):
        return self.id

    def check_password(self, password):
        return self.password == password

class Classifier(Base):
    __tablename__   = "classifier"

    id              = Column(Integer, primary_key = True)
    name            = Column(String(250), index = True)

    owner_id = Column(Integer, ForeignKey("user.id"))

    video = relationship("Video", remote_side = [id])
    children = relationship("Classifier")

    parent_id = Column(Integer, ForeignKey("classifier.id"))

    # a string to indicate the network type
    network_type  = Column(String(250))
    # a string to indicate the network structure. To make it compatible, we should use file path
    network_structure  = Column(String(2500))
    # related training parameters (json format): train dataset, test dataset, epoch, learning tate, momentum etc..
    training_parameters   = Column(String(2500))
    # training status: waiting, training, finished..
    training_status   = Column(Integer, default=0)

    # trained output in a json format: model path, roc path, label file
    training_output   = Column(String(2500))

    container_id   = Column(String(250))


