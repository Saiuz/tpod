from celery_tasks import train_task

# def on_raw_message(body):
#     print "on raw message " + str(body)

task_id = 'slkdfjkdsjf'

t = train_task.apply_async(('1','2','3','4'), task_id=task_id)


# def send_msg_async():
#
#     channel = util.init_communication_channel(task_id)
#     counter = 5
#     while counter > 0:
#         util.send_message(channel, 'tesgwewe', task_id)
#         time.sleep(1)
#         counter -= 1

# thread.start_new_thread(send_msg_async, ())

print '----------------- before calling print -------------'
# print t.get(on_message=on_raw_message, propagate=False)
print '----------------- after calling print -------------'


# import subprocess
#
# proc = subprocess.Popen(['nvidia-docker', 'run', '--rm', 'nvidia/cuda', 'nvidia-smi'])
#
#
# print proc


