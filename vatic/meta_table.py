
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
