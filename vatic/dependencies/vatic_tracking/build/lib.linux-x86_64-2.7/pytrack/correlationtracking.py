import numpy as np
import cv2
from tracking.base import Online
from utils import getframes
from tracking.base import Path
from optflowutil import getpoints, meanshift
import dlib
import vision

MAX_TRACKING_FRAMES=51

# j:
# use dlib's correlation tracking
class CorrelationTracking(Online):
    def track(self, pathid, start, stop, basepath, paths):
        if pathid not in paths:
            return Path(None, None, {})

        path = paths[pathid]

        if start not in path.boxes:
            return Path(path.label, path.id, {})

        startbox = path.boxes[start]
        initialrect = (startbox.xtl, startbox.ytl, startbox.xbr, startbox.ybr)
        # get colored frames
        frames = getframes(basepath, True)
        previmage = frames[start]
        imagesize = previmage.shape

        # intilize dlib tracker
        tracker = dlib.correlation_tracker()
        tracker.start_track(previmage, dlib.rectangle(startbox.xtl, startbox.ytl, startbox.xbr, startbox.ybr))
        boxes={}

        t_stop = min(start+MAX_TRACKING_FRAMES, stop)
        for i in range(start+1,t_stop):
            nextimage=frames[i]
            if nextimage is None:
                break
            tracker.update(nextimage)
            dlib_pos= tracker.get_position()
            (x1, y1, x2,y2)=(int(dlib_pos.left()), int(dlib_pos.top()), int(dlib_pos.right()), int(dlib_pos.bottom()))
            boxes[i] = vision.Box(
                max(0, x1),
                max(0, y1),
                min(imagesize[1], x2),
                min(imagesize[0], y2),
                frame=i,
                generated=True
            )

        # for images over the max tracking number, just use the last image as its labels
        for i in range(t_stop, stop):
            boxes[i] = vision.Box(
                max(0, x1),
                max(0, y1),
                min(imagesize[1], x2),
                min(imagesize[0], y2),
                frame=i,
                generated=True
            )

        # for i in range(start, stop):
        #     image = frames[i]
        #     if i in points:
        #         cv2.circle(image, tuple(forwardmean[i,:]), 6, 0, 3)
        #         for row in points[i]:
        #             cv2.circle(image, tuple(row), 4, 0, 1)

        #     if i in boxes:
        #         box = boxes[i]
        #         cv2.rectangle(image, (box.xtl,box.ytl), (box.xbr,box.ybr), 255,2)

        #     cv2.imshow('correlation tracking', image)
        #     cv2.waitKey(40)
        # cv2.destroyAllWindows()
        
        return Path(path.label, path.id, boxes)
