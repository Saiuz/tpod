import os
import hashlib


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
        if i == len(array) - 1:
            f.write(str(item))
        else:
            f.write(str(item) + '\n')
    f.close()

