from database import Column, Integer, Float, String, Boolean
from database import Model, ForeignKey, Table
from database import relationship, backref

video_evaluation_association_table = Table('video_evaluation_association', 
    Column('evaluation_sets_id', Integer, ForeignKey('evaluation_sets.id')),
    Column('videos_id', Integer, ForeignKey('videos.id'))
)


classifier_evaluation_association_table = Table('classifier_evaluation_association',
    Column('evaluation_sets_id', Integer, ForeignKey('evaluation_sets.id')),
    Column('classifiers_id', Integer, ForeignKey('classifiers.id'))
)

video_classifier_association_table = Table('video_classifier_association',
    Column('videos_id', Integer, ForeignKey('videos.id')),
    Column('classifiers_id', Integer, ForeignKey('classifiers.id'))
)
