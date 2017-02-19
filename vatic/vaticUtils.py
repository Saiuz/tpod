import os
import sys
import math
import argparse
import config
import shutil
from turkic.cli import handler, importparser, Command, LoadCommand
from turkic.database import session
from models import *
from collections import defaultdict
import pdb

def get_video_labels_from_vatic(video_name):
    if session.query(Video).filter(Video.slug == video_name).count():
        video=session.query(Video).filter(Video.slug == video_name).first()
        # check if such label has any paths associated with it
        for label in video.labels:
            existing_labels = [label.text for label in video.labels]
        return existing_labels
    return []

def getvideosinfo(vnames):
    query = session.query(Video).filter(Video.slug.in_(vnames)).all()
    videos_map=defaultdict(lambda: None)
    for video in query:
        print video.slug
        newvideo = {
            "slug": video.slug,
            "segments": [],
        }
        for segment in video.segments:
            newsegment = {
                "start": segment.start,
                "stop":segment.stop,
                "jobs":[],
            }
            for job in segment.jobs:
                newsegment["jobs"].append({
                    "url": job.offlineurl(config.localhost+config.VATIC_URL_PREFIX),
                    "numobjects": len(job.paths),
                    "numdone": len([path for path in job.paths if path.done]),
                })
            newvideo["segments"].append(newsegment)
        videos_map[video.slug]=newvideo
    videos=[videos_map[name] for name in vnames]
    return videos

def vatic_turkic_delete(args):
    video = session.query(Video).filter(Video.slug == args.slug)
    if not video.count():
        print "Video {0} does not exist!".format(args.slug)
        raise ValueError("Video {0} does not exist!".format(args.slug))
    video = video.one()

    query = session.query(Path)
    query = query.join(Job)
    query = query.join(Segment)
    query = query.filter(Segment.video == video)
    numpaths = query.count()
    if numpaths and not args.force:
        print ("Video has {0} paths. Use --force to delete."
            .format(numpaths))
        return False, numpaths

    for segment in video.segments:
        for job in segment.jobs:
            if job.published and not job.completed:
                hitid = job.disable()
                print "Disabled {0}".format(hitid)

    session.delete(video)
    session.commit()

    print "Deleted video and associated data."
    return True, -1

def getlabelsforvideo(vname):
    vids=session.query(Video).filter(Video.slug == vname).all()
    if 0 == len(vids):
        return ''
    elif len(vids) > 1:
        print "Warning: there are more than 1 videos with name {} in the vatic db".format(vname)
    video=vids[0]
    labels=[label.text for label in video.labels]
    return labels

def getnumframesforvideo(vname):
    vids=session.query(Video).filter(Video.slug == vname).all()
    if 0 == len(vids):
        return 0
    elif len(vids) > 1:
        print "Warning: there are more than 1 videos with name {} in the vatic db".format(vname)
    video=vids[0]
    return video.totalframes

