from flask import Flask, request, send_from_directory, render_template, Blueprint
from flask import redirect
from flask.views import View
import simplejson
import os
import cv2
import tempfile
import tracking
import trackutils
from vision.track.interpolation import LinearFill
import cStringIO
from models import *
import dumptools
import numpy as np
import subprocess
import merge
from functools import wraps
import logging
import sys
from extensions import db
from util import shortcache

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config

HOME_BASE = os.path.dirname(os.path.abspath(__file__))
STATIC_BASE = os.path.join(HOME_BASE, 'public')
STATIC_BASE_LEN = len(STATIC_BASE)

vatic_page = Blueprint('vatic_page', __name__, static_folder='public')

logger = logging.getLogger("vatic.server")
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


def vatic_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return simplejson.dumps(func(*args, **kwargs))

    return wrapper


# @vatic_page.before_request
# def before_request():
#     print 'vatic before request'
#     if request.url.startswith('http://'):
#         url = request.url.replace('http://', 'https://', 1)
#         code = 301
#         return redirect(url, code=code)
#
# vatic_page.before_equest(before_request)


def getallvideos():
    session = db.session
    query = session.query(Video)
    videos = []
    for video in query:
        newvideo = {
            "slug": video.slug,
            "segments": [],
        }
        for segment in video.segments:
            newsegment = {
                "start": segment.start,
                "stop": segment.stop,
                "jobs": [],
            }
            for job in segment.jobs:
                newsegment["jobs"].append({
                    "url": job.offlineurl(config.localhost),
                    "numobjects": len(job.paths),
                    "numdone": len([path for path in job.paths if path.done]),
                })
            newvideo["segments"].append(newsegment)
        videos.append(newvideo)
    return videos


handlers = {}


@vatic_page.route("/server/<string:action>", methods=['GET'])
def actions(action):
    session = db.session
    logger.debug('action input {}'.format(action))
    if action in handlers:
        try:
            response = handlers[action]()
        finally:
            session.remove()
        return simplejson.dumps(response)
    return "no such action"


@vatic_page.route("/server/getjob/<int:id>/<int:verified>", methods=['GET'])
def getjob(id, verified):
    session = db.session
    job = session.query(Job).filter(Job.id == id).first()
    if job is None:
        # if it's still not found, return empty
        return 'Job with id %s not found' % str(id)

    logger.debug("Found job {0}".format(job.id))

    if int(verified) and job.segment.video.trainwith:
        # swap segment with the training segment
        training = True
        segment = job.segment.video.trainwith.segments[0]
        logger.debug("Swapping actual segment with training segment")
    else:
        training = False
        segment = job.segment

    video = segment.video
    labels = dict((l.id, l.text) for l in video.labels)

    attributes = {}
    for label in video.labels:
        attributes[label.id] = dict((a.id, a.text) for a in label.attributes)
    print 'got labels %s, there are %s labels for video ' % (str(attributes), str(video.labels))

    logger.debug("Giving user frames {0} to {1} of {2}".format(video.slug,
                                                               segment.start,
                                                               segment.stop))
    homography = video.gethomography()
    # j: disabled hoomography    
    homography = None
    if homography is not None:
        homography = homography.tolist()

    # j: do not return any bidirectional tracker
    trackers = tracking.api.gettrackers()
    trackers['bidirectional'] = {}
    logger.debug("available trackers: {}".format(trackers))

    msg = {
        "start": segment.start,
        "stop": segment.stop,
        "slug": video.slug,
        "width": video.width,
        "height": video.height,
        "skip": video.skip,
        "perobject": video.perobjectbonus,
        "completion": video.completionbonus,
        "blowradius": video.blowradius,
        "jobid": job.id,
        "training": int(training),
        "labels": labels,
        "attributes": attributes,
        "homography": homography,
        "trackers": trackers,
        "nextid": video.nextid(),
        "pointmode": int(video.pointmode),
    }
    return simplejson.dumps(msg)


@vatic_page.route("/server/getboxesforjob/<int:id>", methods=['GET'])
@vatic_handler
def getboxesforjob(id):
    session = db.session
    job = session.query(Job).get(id)
    result = []

    # jj: tmp fix for xtl smaller than 0
    # for path in job.paths:
    #     for box in path.boxes:
    #         if box.xtl < 0:
    #             print 'path id: {}, box id: {}'.format(path.id, box.id)
    #             box.xtl=0
    # session.add(job)
    # session.commit()

    for path in job.paths:
        if path.label is None:
            # there are some paths with no label related, this would result in strange boxes at frontend
            continue
        attrs = [(x.attributeid, x.frame, x.value) for x in path.attributes]
        result.append({"label": path.labelid,
                       "userid": path.userid,
                       "done": path.done,
                       "boxes": [tuple(x) for x in path.getboxes()],
                       "attributes": attrs})
        print 'get path id %s, userid %s attributes %s, label name %s ' % (
        str(path.id), str(path.userid), str(attrs), str(path.label))
    return result


def readpath(label, userid, done, track, attributes):
    #    logger.debug('{} {} {} {}'.format(label,userid,done,attributes))
    session = db.session
    path = Path()

    path.label = session.query(Label).get(label)
    path.done = int(done)
    path.userid = int(userid)

    #    logger.debug("Received {0} track".format(path.label.text))

    visible = False
    for frame, userbox in track.items():
        box = Box(path=path)
        # box.xtl = max(int(userbox[0]), 0)
        # box.ytl = max(int(userbox[1]), 0)
        # box.xbr = max(int(userbox[2]), 0)
        # box.ybr = max(int(userbox[3]), 0)
        box.xtl = int(userbox[0])
        box.ytl = int(userbox[1])
        box.xbr = int(userbox[2])
        box.ybr = int(userbox[3])

        box.occluded = int(userbox[4])
        box.outside = int(userbox[5])
        box.generated = int(userbox[6])
        box.frame = int(frame)
        if not box.outside:
            visible = True

            #        logger.debug("Received box {0}".format(str(box.getbox())))

    if not visible:
        logger.warning("Received empty path! Skipping")
        return None

    for attributeid, timeline in attributes.items():
        attribute = session.query(Attribute).get(attributeid)
        for frame, value in timeline.items():
            aa = AttributeAnnotation()
            aa.attribute = attribute
            aa.frame = frame
            aa.value = value
            path.attributes.append(aa)
    return path


def readpaths(tracks):
    #    logger.debug("Reading {0} total tracks".format(len(tracks)))
    # j: 
    #    for track in tracks:
    #        logger.debug("track content: {}".format(track))
    for label, userid, done, track, attributes in tracks:
        logger.debug("label {}".format(label))
        logger.debug("userid {}".format(userid))
        logger.debug("done {}".format(done))
        logger.debug("track length {}".format(len(track)))
        logger.debug("attributes {}".format(attributes))
    paths = [readpath(label, userid, done, track, attributes) for label, userid, done, track, attributes in tracks]
    return paths


@vatic_page.route("/server/savejob/<int:id>", methods=['POST'])
@vatic_handler
def savejob(id):
    session = db.session
    tracks = request.get_json(force=True)
    job = session.query(Job).get(id)

    logger.debug("job: {} ".format(job))

    # Update current job
    for path in job.paths:
        if path.id != None:
            session.delete(path)
        else:
            logger.warning("corrupted db? db has a path of id None")
    session.commit()

    for path in readpaths(tracks):
        logger.info(path)
        job.paths.append(path)

    session.add(job)
    session.commit()

    # #j:disable merging with neighboring segments

    # # Update neigboring segments
    # video = job.segment.video
    # prevseg, nextseg = video.getsegmentneighbors(job.segment)

    # mergesegments = [s for s in [prevseg, job.segment, nextseg] if s is not None]
    # updatesegments = [s for s in [prevseg, nextseg] if s is not None]

    # # Create list of merged boxes with given label and userid
    # labeledboxes = []
    # for boxes, paths in merge.merge(mergesegments, threshold=0.8):
    #     path = paths[0]
    #     for p in paths:
    #         if p.job.segmentid == job.segmentid:
    #             path = p
    #             break
    #     labeledboxes.append((path.label, path.userid, boxes))

    # # Remove paths in neighboring segments
    # for segment in updatesegments:
    #     for path in segment.paths:
    #         session.delete(path)
    # session.commit()

    # # Add merged paths to neighboring segments
    # for label, userid, boxes in labeledboxes:
    #     frames = sorted([box.frame for box in boxes])
    #     for segment in updatesegments:
    #         for job in segment.jobs:
    #             path = Path()
    #             path.label = label
    #             path.userid = userid
    #             addedbox = False
    #             for box in boxes:
    #                 if segment.start <= box.frame <= segment.stop:
    #                     newbox = Box(path=path)
    #                     newbox.frombox(box)
    #                     if not box.lost:
    #                         addedbox = True

    #             # Some segments and paths might not overlap
    #             if addedbox:
    #                 # Add in first frame if it's missing
    #                 if (frames[0] < segment.start < frames[-1]
    #                         and segment.start not in frames):
    #                     newbox = Box(path=path)
    #                     newbox.generated = False
    #                     newbox.frombox(
    #                         [box for box in LinearFill(boxes)
    #                         if box.frame == segment.start][0]
    #                     )

    #                 job.paths.append(path)

    #             session.add(job)
    # session.commit()
    return 'success'


@vatic_page.route("/server/validatejob/<int:id>", methods=['POST'])
@vatic_handler
def validatejob(id):
    session = db.session
    tracks = request.data
    job = session.query(Job).get(id)
    paths = readpaths(tracks)

    return job.trainingjob.validator(paths, job.trainingjob.paths)


@vatic_page.route("/server/respawnjob/<int:id>", methods=['GET'])
@vatic_handler
def respawnjob(id):
    session = db.session
    job = session.query(Job).get(id)

    replacement = job.markastraining()
    job.worker.verified = True
    session.add(job)
    session.add(replacement)
    session.commit()

    replacement.publish()
    session.add(replacement)
    session.commit()


@vatic_page.route("/server/trackforward/<int:id>/<int:start>/<string:end>/<string:tracker>/<int:trackid>",
                  methods=['POST'])
@vatic_handler
def trackforward(id, start, end, tracker, trackid):
    session = db.session
    start = int(start)
    trackid = int(trackid)
    job = session.query(Job).get(id)
    segment = job.segment
    video = segment.video

    try:
        end = int(end)
    except ValueError:
        end = segment.stop

    tracks = request.get_json(force=True)
    paths = [path for path in readpaths(tracks) if path is not None]
    paths = trackutils.totrackpaths(paths)

    logger.info("trackforward job info:")
    logger.info("Job Id: {0}".format(id))
    logger.info("Algorithm: {0}".format(tracker))
    logger.info("start frame: {0}".format(start))
    logger.info("end frame: {0}".format(end))
    logger.info("len paths: {0}".format(len(paths)))

    # paths here is only used by tracking api for finding the first frame to do
    # tracking initiliazation0
    outpath = tracking.api.online(tracker, start, end, video.location, trackid, paths)
    path = trackutils.fromtrackpath(outpath, job, start, end)
    attrs = [(x.attributeid, x.frame, x.value) for x in path.attributes]

    #    logger.info("path: {0}".format(path.getboxes()))
    #    logger.info("tracked boxes: {}".format([tuple(x) for x in path.getboxes()]))

    return {
        "label": 0,
        "boxes": [tuple(x) for x in path.getboxes()],
        "attributes": attrs
    }


@vatic_page.route('/frames/<path:path>', methods=['GET'])
@shortcache
def no_cache_video_frames(path):
    if '.' in path:
        public_dir = 'public/frames'
        return send_from_directory(public_dir, path)
    return "Frame not found"


@vatic_page.route('/<path:path>', methods=['GET'])
def public_files(path):
    if '.' in path:
        public_dir = 'public'
        return send_from_directory(public_dir, path)
    return "not a static file"


handlers["getallvideos"] = getallvideos
