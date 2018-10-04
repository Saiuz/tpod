
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

from extensions import db
from database import Column, Integer, Float, String, Boolean
from database import Model, CRUDMixin, ForeignKey, Table
from database import relationship, backref


class TaskStatusRecord(Model, CRUDMixin):
    __tablename__   = "task_status_records"

    id              = Column(Integer, primary_key = True)
    task_id  = Column(String(250))
    classifier_id  = Column(String(250))

    update_time  = Column(db.DateTime())
    body = Column(String(5000))

    '''
         {
            'resource_utility': {
                'process_cpu_percentage': self.proc.cpu_percent(),
                'total_memory': v_mem_info.total,
                'total_memory_used': v_mem_info.used,
                'total_memory_percentage': v_mem_info.percent,
                'total_gpu_memory': gpu_total,
                'total_gpu_memory_used': gpu_total_used,
                'process_memory_percentage': self.proc.memory_percent(),
                'process_gpu_memory_used': gpu_process_usage,
            }
            'update_time': 14xxxxxx,
        }
    '''




