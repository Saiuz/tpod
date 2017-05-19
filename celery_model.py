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




