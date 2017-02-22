import turkic_replacement as api
import db_util
import config


# api.extract('test.mp4', 'test_video')
api.load("test.mp4", 'test_video', ['test_label1', 'test_label2'])


