from celery import Task
from celery.signals import task_postrun
from celery.utils.log import get_task_logger
import datetime
import subprocess
import time
import psutil
import util
import thread
import sys
from celery_model import TaskStatusRecord
import docker
import re
import json
import random
import config
import requests

from extensions import db, tpod_celery

logger = get_task_logger('tpod')

TASK_TYPE_NONE = 1
TASK_TYPE_TRAIN = 2
TASK_TYPE_TEST = 3
TASK_TYPE_EVALUATION = 4

STATE_NONE = 'NONE'
STATE_START = 'START'
STATE_PROGRESS = 'PROGRESS'
STATE_FINISH = 'FINISH'
STATE_ERROR = 'ERROR'

# http://stackoverflow.com/questions/12044776/how-to-use-flask-sqlalchemy-in-a-celery-task
@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from 
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors 
    # won't propagate across tasks)
    db.session.remove()
    
class TPODBaseTask(Task):
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

    def __call__(self, *args, **kwargs):
        logger.info('Starting Task: {0.name},type:{0.task_type},[{0.request.id}]'.format(self))
        self.task_id = self.request.id
        return super(TPODBaseTask, self).__call__(*args, **kwargs)

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
            "resource_utility": {
                "total_memory": "0",
                "total_memory_used": "0",
                "total_memory_percentage": "0",
                "total_gpu_memory": "0",
                "total_gpu_memory_used": "0",
                "process_cpu_percentage": "0",
                "process_memory_percentage": "0",
                "process_gpu_memory_used": "",
            },
            "status": self.status,
            "container_status": None,
            "pid": -1,
        }
        if self.pid is None or not psutil.pid_exists(self.pid):
            return ret

        try:
            if self.proc is None:
                self.proc = psutil.Process(self.pid)
            ret["pid"] = self.pid

            v_mem_info = psutil.virtual_memory()
            gpu_total_used, gpu_total, gpu_process_usage = util.get_gpu_info(self.pid)
            ret["resource_utility"]["process_cpu_percentage"] = self.proc.cpu_percent(),
            ret["resource_utility"]["total_memory"] = v_mem_info.total
            ret["resource_utility"]["total_memory_used"] = v_mem_info.used
            ret["resource_utility"]["total_memory_percentage"] = v_mem_info.percent
            ret["resource_utility"]["total_gpu_memory"] = gpu_total
            ret["resource_utility"]["total_gpu_memory_used"] = gpu_total_used
            ret["resource_utility"]["process_memory_percentage"] = self.proc.memory_percent()
            ret["resource_utility"]["process_gpu_memory_used"] = gpu_process_usage
            if self.container is not None:
                ret["container_status"] = self.container.status
                print 'container status ' + str(self.container.status)
            return ret
        except Exception as e:
            print e
        return ret

    def read_logs(self):
        try:
            log = None
            if self.last_read_log_time is None:
                log = self.container.logs(timestamps=True)
            else:
                log = self.container.logs(timestamps=True, since=self.last_read_log_time)
            self.last_read_log_time = int(time.time())
            return log
        except Exception as e:
            print e

    def update_status(self, state):
        self.status = state
        content = str(json.dumps(self.get_process_status()))
        print "get update " + content
        status = TaskStatusRecord(task_id=self.task_id, classifier_id=self.classifier_id)
        status.update_time = datetime.datetime.now()
        status.body = content
        session = db.session
        session.add(status)
        session.commit()


class TPODTrainingTask(TPODBaseTask):
    def __init__(self):
        super(TPODTrainingTask, self).__init__()
        self.total_iteration = -1
        self.iteration = -1
        self.loss = -1
        self.training_finish_detected = False

    def init_task(self, classifier_id, train_set_name, epoch, weights):
        self.task_type = TASK_TYPE_TRAIN
        self.classifier_id = classifier_id
        self.total_iteration = epoch

        self.update_status(STATE_START)
        self.init_message_callback()

    def get_process_status(self):
        ret = super(TPODTrainingTask, self).get_process_status()
        ret['iteration'] = self.iteration
        ret['loss'] = self.loss
        return ret

    def read_logs(self):
        log = super(TPODTrainingTask, self).read_logs()
        # analysis the log
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
                self.iteration = self.total_iteration
                print 'training finish signal detected'
        return log


@tpod_celery.task(bind=True, base=TPODTrainingTask)
def train_task(self, base_image_name, result_image_name, dataset_path, classifier_id, train_set_name, epoch, weights):
    self.init_task(classifier_id, train_set_name, epoch, weights)
    # example command inside the docker
    # /usr/bin/python tools/tpod_train_net.py --weights /VGG_CNN_M_1024.v2.caffemodel --output_dir .
    # --iter 2000 --train_set_name 1492198
    docker_name = result_image_name

    docker_data_volume = str(dataset_path) + ':/dataset'
    proc = subprocess.Popen(['nvidia-docker', 'run', '-v', docker_data_volume, '--name', docker_name,
                             base_image_name, '/usr/bin/python', 'tools/tpod_train_net.py', '--weights', str(weights),
                             '--output_dir', '.', '--iter', str(epoch), '--train_set_name', str(train_set_name)])
    # bind the docker api
    client = docker.from_env()

    # wait for the docker to launch
    time.sleep(2)
    try:
        self.container = client.containers.get(docker_name)
    except Exception as e:
        print 'attach container error: ' + str(e)
        proc.terminate()
        self.update_status(STATE_FINISH)

    # actually, the process executing the cmd is not the process the container is running,
    # thus we need find and rebind the process
    # since we are running only one process inside the container, it's feasible to hard code the index of the process
    top = self.container.top()
    self.pid = int(top['Processes'][0][1])

    print 'launching training task with pid %s train set %s, epoch %s, weights %s' % (str(self.pid),
                                                                                      str(train_set_name), str(epoch),
                                                                                      str(weights))
    # begin monitoring the status of the process
    while self.container.status == 'running' and not self.training_finish_detected and psutil.pid_exists(self.pid):
        self.read_logs()
        self.update_status(STATE_PROGRESS)
        time.sleep(1 / float(self.monitor_rate))
    if self.iteration <= 0:
        # something wrong happened during launch
        self.update_status('ERROR during launch')
    else:
        # works correctly, commit the image
        commit_message = 'commit from task %s, at time %s ' % (str(self.task_id), str(datetime.datetime.now()))
        self.container.commit(author='tpod_task', message=commit_message, repository=docker_name)

        self.update_status(STATE_FINISH)
    # stop and remove the container
    self.container.stop()
    self.container.remove()
    proc.terminate()


class TPODTestTask(TPODBaseTask):
    def __init__(self):
        super(TPODTestTask, self).__init__()
        # the length of time the server will run
        # -1 means running forever
        self.time_remains = 10
        # the number of request perceived from the log
        self.request_number = 0
        self.host_port = -1

    def init_task(self, classifier_id, host_port, time_remains=10):
        self.task_type = TASK_TYPE_TEST
        self.classifier_id = classifier_id
        self.time_remains = time_remains
        self.host_port = host_port

        self.update_status(STATE_START)
        self.init_message_callback()

    def get_process_status(self):
        ret = super(TPODTestTask, self).get_process_status()
        ret['request_number'] = self.request_number
        ret['time_remains'] = self.time_remains
        ret['host_port'] = self.host_port
        return ret

    def read_logs(self):
        log = super(TPODTestTask, self).read_logs()
        # analysis the log
        return log


@tpod_celery.task(bind=True, base=TPODTestTask)
def test_task(self, classifier_id, docker_image_id, time_remains, host_port):
    self.init_task(classifier_id, host_port, time_remains)

    docker_name = str(self.task_id)

    container_port = 8000

    image_name = str(docker_image_id)
    example_cmd = 'nvidia-docker run -p %s --name %s %s /bin/bash run_server.sh' % (
        str(host_port) + ':' + str(container_port), str(docker_name), str(image_name))
    print 'example cmd: %s ' % example_cmd
    proc = subprocess.Popen(['nvidia-docker', 'run', '-p', str(host_port) + ':' + str(container_port), '--name',
                             docker_name, image_name,
                             '/bin/bash', 'run_server.sh'])

    # bind the docker api
    client = docker.from_env()

    # wait for the docker to launch
    time.sleep(2)
    try:
        self.container = client.containers.get(docker_name)
    except Exception as e:
        print 'attach container error: ' + str(e)
        proc.terminate()
        self.update_status(STATE_FINISH)

    # actually, the process executing the cmd is not the process the container is running,
    # thus we need find and rebind the process
    # since we are running only one process inside the container, it's feasible to hard code the index of the process
    top = self.container.top()
    self.pid = int(top['Processes'][0][1])

    print 'launching training task with pid %s, docker_image_name %s, time_remains %s, host_port %s' % \
          (str(self.pid), str(docker_image_id), str(time_remains), str(host_port))
    # begin monitoring the status of the process
    while self.container.status == 'running' and psutil.pid_exists(self.pid) and self.time_remains > 0:
        self.read_logs()
        self.update_status(STATE_PROGRESS)
        time.sleep(1 / float(self.monitor_rate))
        self.time_remains -= (1 / float(self.monitor_rate))

    # since this is a test task, just remove it
    # stop and remove the container
    self.container.remove(force=True)

    proc.terminate()
    self.update_status(STATE_FINISH)


class TPODEvaluationTask(TPODBaseTask):
    def __init__(self):
        super(TPODEvaluationTask, self).__init__()
        self.evaluation_set_name = None
        self.evaluation_result_name = None

    def init_task(self, classifier_id, evaluation_set_name, evaluation_result_name):
        self.task_type = TASK_TYPE_EVALUATION
        self.classifier_id = classifier_id
        self.evaluation_set_name = evaluation_set_name
        self.evaluation_result_name = evaluation_result_name

        self.update_status(STATE_START)
        self.init_message_callback()

    def get_process_status(self):
        ret = super(TPODEvaluationTask, self).get_process_status()
        # ret['request_number'] = self.request_number
        return ret

    def read_logs(self):
        log = super(TPODEvaluationTask, self).read_logs()
        # analysis the log
        return log


@tpod_celery.task(bind=True, base=TPODEvaluationTask)
def evaluation_task(self, dataset_path, eval_path, classifier_id, docker_image_id, evaluation_set_name, evaluation_result_name):
    '''
    :param self:
    :param classifier_id: the classifier to evaluate
    :param docker_image_id: the id of the docker image
    :param evaluation_set_name: the name of evaluation set
    :param evaluation_result_name: the name for the evaluation result, since it will be stored in the 'evaluation' folder
    :return: the status of execution
    '''
    self.init_task(classifier_id, evaluation_set_name, evaluation_result_name)

    docker_name = str(self.task_id)

    image_name = docker_image_id

    docker_data_volume = str(dataset_path) + ':/dataset'
    docker_data_volume_eval = str(eval_path) + ':/eval'
    example_cmd = 'python tools/tpod_eval_net.py --gpu 0 --output_dir . --eval_set_name %s --eval_result_name %s ' % \
                  (str(evaluation_set_name), str(evaluation_result_name))
    print 'execute: %s ' % str(example_cmd)
    proc = subprocess.Popen(['nvidia-docker', 'run', '-v', docker_data_volume, '-v', docker_data_volume_eval, '--name',
                             docker_name, image_name,
                             'python', 'tools/tpod_eval_net.py', '--gpu', '0', '--output_dir', '.', '--eval_set_name',
                             str(evaluation_set_name), '--eval_result_name', str(evaluation_result_name)])

    # bind the docker api
    client = docker.from_env()

    # wait for the docker to launch
    time.sleep(2)
    try:
        self.container = client.containers.get(docker_name)
    except Exception as e:
        print 'attach container error: ' + str(e)
        proc.terminate()
        self.update_status(STATE_FINISH)

    # actually, the process executing the cmd is not the process the container is running,
    # thus we need find and rebind the process
    # since we are running only one process inside the container, it's feasible to hard code the index of the process
    top = self.container.top()
    self.pid = int(top['Processes'][0][1])

    print 'launching evaluation task with pid %s, classifier id %s, evaluation set %s, evaluation result name %s' % \
          (str(self.pid), str(classifier_id), str(evaluation_set_name), str(evaluation_result_name))
    # begin monitoring the status of the process
    while self.container.status == 'running' and psutil.pid_exists(self.pid):
        self.read_logs()
        self.update_status(STATE_PROGRESS)
        time.sleep(1 / float(self.monitor_rate))

    # since this is a test task, just remove it
    # stop and remove the container
    self.container.remove(force=True)

    proc.terminate()
    self.update_status(STATE_FINISH)


@tpod_celery.task(trail=True)
def push_image_task(image_name, push_tag_name):
    client = docker.from_env()
    print 'begin pushing image'
    print 'image name %s ' % str(image_name)
    try:
        image = client.images.get(str(image_name))
        tag_name = 'registry.cmusatyalab.org/junjuew/container-registry:%s' % str(push_tag_name)
        print 'tag name %s ' % str(push_tag_name)
        image.tag(tag_name)
        ret = client.images.push(tag_name)
        print 'end pushing image'
        print ret
        return ret
    except Exception as e:
        print e
    return False

