# -*- coding: utf-8 -*-
import os
import hashlib
import subprocess
import re
import pika
import socket
import requests
import time
from functools import wraps, update_wrapper
from datetime import datetime

from flask import make_response

import docker
import m_logger

logger = m_logger.get_logger('UTIL')


def get_file_size(file_name):
    stat = os.stat(file_name)
    return stat.st_size


def get_file_md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def is_video_file(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension.lower() == '.mp4' or file_extension.lower() == '.avi' or file_extension.lower() == '.m4v'


def is_image_file(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension.lower() == '.png' or file_extension.lower() == '.jpg' or file_extension.lower() == '.jpeg'


def is_zip_file(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension.lower() == '.zip'


def write_list_to_file(array, file_path):
    f = open(file_path, 'w+')
    for i in range(0, len(array)):
        item = array[i]
        # if i == len(array) - 1:
        #     f.write(str(item))
        # else:
        f.write(str(item) + '\n')
    f.close()

'''
+-----------------------------------------------------------------------------+      │
| NVIDIA-SMI 375.26                 Driver Version: 375.26                    |      │
|-------------------------------+----------------------+----------------------+      │
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |      │
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |      │
|===============================+======================+======================|      │
|   0  GeForce GTX 960     On   | 0000:03:00.0      On |                  N/A |      │
| 22%   25C    P8     9W / 130W |     50MiB /  1995MiB |      0%      Default |      │
+-------------------------------+----------------------+----------------------+      │
                                                                                     │
+-----------------------------------------------------------------------------+      │
| Processes:                                                       GPU Memory |      │
|  GPU       PID  Type  Process name                               Usage      |      │
|=============================================================================|      │
|    0      2293    G   /usr/bin/X                                      48MiB |      │
+-----------------------------------------------------------------------------+      │
'''


def get_gpu_info(pid):
    output = subprocess.check_output(['nvidia-smi'])
    total = 0
    total_used = 0
    # first get the total usagej
    total_usage_match = re.search(r'(\d+)MiB\s*\/\s*(\d+)MiB', output, re.M|re.I)
    if total_usage_match:
        total_used = int(total_usage_match.group(1))
        total = int(total_usage_match.group(2))

    process_usages_match = re.findall(r'\|\s+\d+\s*(\d+)\s+[^\s]+\s+[^\s]+\s+(\d+)MiB', output, re.DOTALL)
    process_usage = 0
    if process_usages_match:
        for match in process_usages_match:
            current_pid = int(match[0])
            gpu_usage = (match[1])
            if current_pid == pid:
                process_usage = gpu_usage
                break
    return total_used, total, process_usage


def init_communication_channel(task_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
    channel = connection.channel()
    queue_id = 'queue_' + str(task_id)
    channel.queue_declare(queue=queue_id)
    return channel


def send_message(channel, msg, task_id):
    queue_id = 'queue_' + str(task_id)
    channel.basic_publish(exchange='',
                          routing_key=queue_id,
                          body=msg)


def register_message_callback(callback, channel, task_id):
    queue_id = 'queue_' + str(task_id)
    consumer_tag = channel.basic_consume(callback,
                          queue=queue_id,
                          no_ack=True)
    channel.start_consuming()
    return consumer_tag


def get_available_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.bind(('', 0))
    _, port = sock.getsockname()
    sock.close()
    return port


def get_request_result_multiple_trials(url, payload, files, file_name, trials=5, interval=5):
    attempt = 0
    success = False
    while attempt < trials:
        try:
            get_request_result(url, payload, files, file_name)
            success = True
            break
        except requests.exceptions.ConnectionError as e:
            print 'connection error for POST request to {}'.format(url)
            # seek to 0 for all files
            map(lambda (k,v): v.seek(0), files.iteritems())
            time.sleep(interval)
        attempt += 1
    print 'successfully get POST message response after {} trials? {}'.format(trials, success)
    return success
    

def get_request_result(url, payload, files, file_name):
    print 'payload: {}'.format(payload)
    print 'files: {}'.format(files)
    print 'file_name: {}'.format(file_name)
    r = requests.post(url, data=payload, files=files)
    f = open(file_name, 'wb')
    chunk_size = 1000
    for chunk in r.iter_content(chunk_size=chunk_size):
        f.write(chunk)
    f.close()
    print 'successfully get POST result from {}'.format(url)


def get_unique_label_name(label_array):
    label_ret = []
    for label in label_array:
        if label not in label_ret:
            label_ret.append(label)
    return label_ret


def get_dataset_path():
    return os.getcwd() + '/dataset/'


def get_eval_path():
    return os.getcwd() + '/eval/'


def get_classifier_image_name(classifier_name, classifier_id):
    result_image_name = str(classifier_name) + '-id-' + str(classifier_id)
    result_image_name = result_image_name.lower()
    return result_image_name


def safe_docker_image_name(name):
    return str(name).lower()


def remove_file_if_exist(fpath):
    if os.path.exists(fpath) and os.path.isfile(fpath):
        os.remove(fpath)


def has_container_image(image_name):
    client = docker.from_env()
    found = True
    try:
        client.images.get(str(image_name))
    except docker.errors.ImageNotFound:
        found = False
    return found

        
def issue_blocking_cmd(cmd):
    if isinstance(cmd, str):
        cmd = cmd.split(" ")
    logger.debug("issuing cmd: {}".format(' '.join(cmd)))
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    error_code = p.wait()
    logger.debug("error_code: {}".format(error_code))
    logger.debug("stdout: {}".format(stdout))
    logger.debug("stderr: {}".format(stderr))
    return error_code

def shortcache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'public, max-age=300'
        return response
        
    return update_wrapper(no_cache, view) 


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
