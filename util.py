# -*- coding: utf-8 -*-
import os
import hashlib
import subprocess
import re
import pika


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

