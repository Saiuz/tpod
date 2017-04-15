from db_util import Base
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, BigInteger


class TaskStatusRecord(Base):
    __tablename__   = "task_status_records"

    id              = Column(Integer, primary_key = True)
    task_id  = Column(String(250))
    classifier_id  = Column(String(250))

    update_time  = DateTime()

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
        }
    '''




