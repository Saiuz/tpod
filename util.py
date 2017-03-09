import os

def get_file_size(file_name):
    stat = os.stat(file_name)
    return stat.st_size






