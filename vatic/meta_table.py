from sqlalchemy import Column, Integer, Float, String, Boolean
from sqlalchemy import ForeignKey, Table, PickleType
from sqlalchemy.orm import relationship, backref
from db_util import Base


video_evaluation_association_table = Table('video_evaluation_association', Base.metadata,
    Column('evaluation_sets_id', Integer, ForeignKey('evaluation_sets.id')),
    Column('videos_id', Integer, ForeignKey('videos.id'))
)


classifier_evaluation_association_table = Table('classifier_evaluation_association', Base.metadata,
    Column('evaluation_sets_id', Integer, ForeignKey('evaluation_sets.id')),
    Column('classifiers_id', Integer, ForeignKey('classifiers.id'))
)




