from celery import Celery
from celery import Task
from celery.utils.log import get_task_logger
import datetime
import subprocess
import time
import psutil
import util
import thread
import sys
from celery_model import TaskStatusRecord
import db_util
import docker
import re

app = Celery('tpod_task', broker='amqp://localhost', backend='rpc://localhost')
logger = get_task_logger('tpod')

TASK_TYPE_NONE = 1
TASK_TYPE_TRAIN = 2
TASK_TYPE_TEST = 3

STATE_NONE = 'NONE'
STATE_START = 'START'
STATE_PROGRESS = 'PROGRESS'
STATE_FINISH = 'FINISH'


class TPODTask(Task):

    def __init__(self):
        self.task_type = TASK_TYPE_NONE
        self.pid = None
        self.proc = None
        self.monitor_rate = 1
        self.task_id = None
        self.classifier_id = None
        self.status = None
        self.container = None
        self.last_read_log_time = None
        self.total_iteration = -1
        self.iteration = -1
        self.loss = -1
        self.training_finish_detected = False

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
        print 'updating the status of task %s, with pid %s ' % (str(self.task_id), str(self.pid))
        ret = {
            'resource_utility': {
                'process_cpu_percentage': '0',
                'total_memory': '0',
                'total_memory_used': '0',
                'total_memory_percentage': '0',
                'total_gpu_memory': '0',
                'total_gpu_memory_used': '0',
                'process_memory_percentage': '0',
                'process_gpu_memory_used': '',
            },
            'status': self.status,
            'container_status': None,
            'iteration': self.iteration,
            'loss': self.loss,
        }
        if self.pid is None:
            return ret

        if self.proc is None:
            self.proc = psutil.Process(self.pid)

        v_mem_info = psutil.virtual_memory()
        gpu_total_used, gpu_total, gpu_process_usage = util.get_gpu_info(self.pid)
        ret['resource_utility']['process_cpu_percentage'] = self.proc.cpu_percent(),
        ret['resource_utility']['total_memory']= v_mem_info.total
        ret['resource_utility']['total_memory_used']= v_mem_info.used
        ret['resource_utility']['total_memory_percentage']= v_mem_info.percent
        ret['resource_utility']['total_gpu_memory']= gpu_total
        ret['resource_utility']['total_gpu_memory_used']= gpu_total_used
        ret['resource_utility']['process_memory_percentage']= self.proc.memory_percent()
        ret['resource_utility']['process_gpu_memory_used']= gpu_process_usage
        if self.container is not None:
            ret['container_status'] = self.container.status
            print 'conntainer status ' + str(self.container.status)
        return str(ret)

    def read_logs(self):
        try:
            log = None
            if self.last_read_log_time is None:
                log = self.container.logs(timestamps=True)
            else:
                log = self.container.logs(timestamps=True, since=self.last_read_log_time)
            self.last_read_log_time = int(time.time())

            # analysis the log
            #Iteration 20, loss = 0.967152
            iteration_match = re.findall(r'Iteration\s*(\d+),?\s*loss[^\d]+([\d,\.]+)', log, re.DOTALL)
            if iteration_match:
                for match in iteration_match:
                    self.iteration = int(match[0])
                    self.loss = float(match[1])
                    print 'iteration %s, loss %s, total iteration %s' % \
                          (str(self.iteration), str(self.loss), str(self.total_iteration))

            # check if training finishes, to avoid accident print of this signal,
            # we also check if the iteration is mostly executed
            if log is not None and int(self.total_iteration) > 0 and \
                int(self.total_iteration) - int(self.iteration) <= 40:
                finish_match = re.findall(r'done\ssolving', log, re.DOTALL)
                if len(finish_match) > 0:
                    self.training_finish_detected = True
                    print 'training finish signal detected'

            return log
        except Exception as e:
            print e

    def update_status(self, state):
        self.status = state
        content = str(self.get_process_status())
        session = db_util.renew_session()
        status = TaskStatusRecord(task_id = self.task_id, classifier_id = self.classifier_id)
        status.update_time = datetime.datetime.now()
        status.body = content
        session.add(status)
        session.commit()
        session.close()


@app.task(bind=True, base=TPODTask)
def train_task(self, classifier_id, train_set_name, epoch, weights):
    self.task_type = TASK_TYPE_TRAIN
    self.classifier_id = classifier_id
    self.total_iteration = epoch

    self.update_status(STATE_START)
    self.init_message_callback()
    # example command inside the docker
    # /usr/bin/python tools/tpod_train_net.py --weights /VGG_CNN_M_1024.v2.caffemodel --output_dir . --iter 2000 --train_set_name 1492198
    docker_name = str(self.task_id)

    # cmd = '/usr/bin/python tools/tpod_train_net.py --weights %s --output_dir . --iter %s --train_set_name %s' % \
    #       (str(weights), str(epoch), str(train_set_name))
    # proc = subprocess.Popen(['nvidia-docker', 'run', '--name', docker_name, 'nvidia/cuda', 'nvidia-smi'])

    docker_data_volume = '/home/suanmiao/workspace/tpod/dataset/:/dataset'
    image_name = 'faster-rcnn-base'
    proc = subprocess.Popen(['nvidia-docker', 'run', '-v', docker_data_volume, '--name', docker_name,
                             image_name, '/usr/bin/python', 'tools/tpod_train_net.py', '--weights', str(weights),
                             '--output_dir', '.', '--iter', str(epoch), '--train_set_name', str(train_set_name)])
    # bind the docker api
    client = docker.from_env()

    # wait for the docker to launch
    time.sleep(3)
    try:
        self.container = client.containers.get(docker_name)
    except Exception as e:
        print 'attach container error: ' + str(e)
        proc.terminate()
        self.update_status(STATE_FINISH)

    # if self.container.status == 'exited':
    # self.container.start()
    # self.container.exec_run(cmd)

    self.pid = proc.pid
    print 'launching training task with pid %s train set %s, epoch %s, weights %s' % (str(self.pid),
                                                                                      str(train_set_name), str(epoch), str(weights))
    # begin monitoring the status of the process
    while self.container.status == 'running' and not self.training_finish_detected:
        self.read_logs()
        self.update_status(STATE_PROGRESS)
        time.sleep(1/float(self.monitor_rate))

    commit_message = 'commit from task %s, at time %s ' %(str(self.task_id), str(datetime.datetime.now()))
    self.container.commit(author='tpod_task', message= commit_message, repository= docker_name)
    if self.container.status == 'exited':
        print 'the container is exited, we will remove the container'
        # remove the container
        self.container.remove()

    proc.terminate()
    self.update_status(STATE_FINISH)




