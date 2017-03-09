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
    return file_extension.lower() == '.mp4' or file_extension.lower() == '.avi'


def is_zip_file(file_name):
    file_name, file_extension = os.path.splitext(file_name)
    return file_extension.lower() == '.zip'


