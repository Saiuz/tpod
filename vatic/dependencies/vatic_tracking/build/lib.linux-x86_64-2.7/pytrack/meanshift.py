import numpy as np
import cv2
from tracking.base import Path
from tracking.base import Online
from utils import getframes
import vision

class CamShift(Online):
    def track(self, pathid, start, stop, basepath, paths):
        if pathid not in paths:
            return Path(None, None, {})

        path = paths[pathid]

        if start not in path.boxes:
            return Path(path.label, path.id, {})

        startbox = path.boxes[start]
        rect = (startbox.xtl, startbox.ytl, startbox.xbr-startbox.xtl+1, startbox.ybr-startbox.ytl+1)
        # get colored frames
        frames = getframes(basepath, True)
        previmage = frames[start]
        imagesize = previmage.shape

        cv2.rectangle(previmage, (startbox.xtl,startbox.ytl), (startbox.xbr,startbox.ybr), 255,2)
        cv2.imshow('initialize', previmage)
        
        # set up the ROI for tracking
        roi = previmage[startbox.ytl:startbox.ybr+1, startbox.xtl:startbox.xbr+1]
        hsv_roi =  cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_roi, np.array((0., 60.,32.)), np.array((180.,255.,255.)))
        roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0,180])
        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
 
        # Setup the termination criteria, either 10 iteration or move by atleast 1 pt
        term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

        boxes={}
        for i in range(start+1, stop):
            nextimage=frames[i]
            if nextimage is None:
                break

            hsv = cv2.cvtColor(nextimage, cv2.COLOR_BGR2HSV)
            dst = cv2.calcBackProject([hsv], [0], roi_hist, [0,180], 1)

            # apply meanshift to get the new location
#            ret, rect = cv2.meanShift(dst, rect, term_crit)
            ret, rect = cv2.CamShift(dst, rect, term_crit)

            # tracker failed
#            if not ret:
#                break
            
            x1,y1,w,h=rect
            x2=x1+w-1
            y2=y1+h-1
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
        #     if i in boxes:
        #         box = boxes[i]
        #         cv2.rectangle(image, (box.xtl,box.ytl), (box.xbr,box.ybr), 255,2)
        #     cv2.imshow('meanshift tracking', image)
        #     cv2.waitKey(40)
#        cv2.destroyAllWindows()

        return Path(path.label, path.id, boxes)
