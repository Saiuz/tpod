from celery import Celery
from celery import Task
from celery.utils.log import get_task_logger

import subprocess
import time
import psutil
import util
import thread

app = Celery('tpod_task', broker='amqp://localhost', backend='rpc://localhost')
logger = get_task_logger('tpod')

TASK_TYPE_NONE = 1
TASK_TYPE_TRAIN = 2
TASK_TYPE_TEST = 3

STATE_START = 'START'
STATE_PROGRESS = 'PROGRESS'
STATE_FINISH = 'FINISH'


class TPODTask(Task):

    def __init__(self):
        self.task_type = TASK_TYPE_NONE
        self.pid = None
        self.proc = None
        self.counter = 0
        self.running = True
        self.monitor_rate = 1
        self.task_id = None

    def __call__(self, *args, **kwargs):
        logger.info('Starting Task: {0.name},type:{0.task_type},[{0.request.id}]'.format(self))
        self.task_id = self.request.id
        return super(TPODTask, self).__call__(*args, **kwargs)

    def init_message_callback(self):
        def register_callback_async():
            channel = util.init_communication_channel(self.task_id)

            def callback(ch, method, properties, body):
                print(" [x] Received %r" % body)

            logger.info('Registered callback with task id {0} '.format(self))
            self.consumer_tag = util.register_message_callback(callback, channel, self.task_id)
        thread.start_new_thread(register_callback_async, ())

    def get_process_status(self):
        if self.proc is None:
            self.proc = psutil.Process(self.pid)
        v_mem_info = psutil.virtual_memory()

        gpu_total_used, gpu_total, gpu_process_usage = util.get_gpu_info(2293)
        ret = {
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
        return str(ret)

    def update_status(self, state):
        return self.update_state(state=state, meta=self.get_process_status(), task_id=self.request.id)


@app.task(bind=True, base=TPODTask)
def train_task(self, a, b):
    self.task_type = TASK_TYPE_TRAIN

    self.update_status(STATE_START)
    self.init_message_callback()

    # begin the process
    proc = subprocess.Popen(['python', 'test_process.py'])
    self.pid = proc.pid

    # begin monitoring the status of the process
    while self.running:
        self.update_status(STATE_PROGRESS)
        time.sleep(1/float(self.monitor_rate))
        self.counter += 1
        if self.counter == 10:
            self.running = False
    ## TODO: might need to kill children process too
    proc.terminate()
    self.update_status(STATE_FINISH)

    return str(a) + str(b)



