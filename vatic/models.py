import logging
import os
import api

import numpy as np
import vision
from PIL import Image
from database import Column, Integer, Float, String, Boolean
from database import Model, CRUDMixin, ForeignKey, Table
from database import relationship, backref
from vision.track.interpolation import LinearFill
from meta_table import video_evaluation_association_table

import config

logger = logging.getLogger("vatic.models")

boxes_attributes = Table("boxes2attributes", 
    Column("box_id", Integer, ForeignKey("boxes.id")),
    Column("attribute_id", Integer, ForeignKey("attributes.id")))

class Video(Model, CRUDMixin):
    __tablename__   = "videos"

    id              = Column(Integer, primary_key = True)
    slug            = Column(String(250), index = True)
    width           = Column(Integer)
    height          = Column(Integer)
    totalframes     = Column(Integer)
    location        = Column(String(250))
    skip            = Column(Integer, default = 0, nullable = False)
    perobjectbonus  = Column(Float, default = 0)
    completionbonus = Column(Float, default = 0)
    trainwithid     = Column(Integer, ForeignKey(id))
    trainwith       = relationship("Video", remote_side = id)
    isfortraining   = Column(Boolean, default = False)
    blowradius      = Column(Integer, default = 5)
    homographylocation  = Column(String(250), nullable = True, default = None)
    pointmode       = Column(Boolean, default = False)

    orig_file_path  = Column(String(550))
    extract_path  = Column(String(550))

    # many to one
    owner_id = Column(Integer, ForeignKey("users.id"))
    # many to one
    classifier_id = Column(Integer, ForeignKey("classifiers.id"))
    # many to many
    evaluation_sets = relationship("EvaluationSet", secondary=video_evaluation_association_table, back_populates='videos')

    def __getitem__(self, frame):
        path = Video.getframepath(frame, self.location)
        return Image.open(path)

    @classmethod
    def getframepath(cls, frame, base = None):
        l1 = frame / 10000
        l2 = frame / 100
        path = "{0}/{1}/{2}.jpg".format(l1, l2, frame)
        if base is not None:
            path = "{0}/{1}".format(base, path)
        return path

    @property
    def cost(self):
        cost = 0
        for segment in self.segments:
            cost += segment.cost
        return cost

    @property
    def numjobs(self):
        count = 0
        for segment in self.segments:
            for job in segment.jobs:
                count += 1
        return count

    @property
    def numcompleted(self):
        count = 0
        for segment in self.segments:
            for job in segment.jobs:
                if job.completed:
                    count += 1
        return count

    def gethomography(self):
        if self.homographylocation is not None:
            path = os.path.join(self.homographylocation, "homography.npy")
            if os.path.exists(path):
                return np.load(path)
        return None

    def nextid(self):
        userids = [path.userid for segment in self.segments for path in segment.paths]
        if len(userids) == 0:
            return 0
        return max(userids) + 1

    def getsegmentneighbors(self, segment):
        start, stop  = segment.start, segment.stop
        prevseg, nextseg = None, None
        for seg in self.segments:
            if start <= seg.stop < stop:
                prevseg = seg
            elif start < seg.start <= stop:
                nextseg = seg
        return prevseg, nextseg

class Label(Model, CRUDMixin):
    __tablename__ = "labels"

    id = Column(Integer, primary_key = True)
    text = Column(String(250))
    videoid = Column(Integer, ForeignKey(Video.id))
    video = relationship(Video, backref = backref("labels",
                                                  cascade = "all,delete"))

class Attribute(Model, CRUDMixin):
    __tablename__ = "attributes"

    id = Column(Integer, primary_key = True)
    text = Column(String(250))
    labelid = Column(Integer, ForeignKey(Label.id))
    label = relationship(Label, backref = backref("attributes",
                                                  cascade = "all,delete"))

    def __str__(self):
        return self.text

class Segment(Model, CRUDMixin):
    __tablename__ = "segments"

    id = Column(Integer, primary_key = True)
    videoid = Column(Integer, ForeignKey(Video.id))
    video = relationship(Video, backref = backref("segments",
                                                  cascade = "all,delete"))
    start = Column(Integer)
    stop = Column(Integer)

    @property
    def paths(self):
        paths = []
        for job in self.jobs:
            if job.useful:
                paths.extend(job.paths)
        return paths

    @property
    def cost(self):
        cost = 0
        for job in self.jobs:
            cost += job.cost
        return cost

class Job(Model, CRUDMixin):
    __tablename__ = "jobs"
    __mapper_args__ = {"polymorphic_identity": "jobs"}

    id             = Column(Integer,  primary_key = True)
    segmentid      = Column(Integer, ForeignKey(Segment.id))
    segment        = relationship(Segment,
                                  backref = backref("jobs",
                                                    cascade = "all,delete"))
    istraining     = Column(Boolean, default = False)
    hitid         = Column(String(30))
    assignmentid  = Column(String(30))
    ready         = Column(Boolean, default = True, index = True)
    published     = Column(Boolean, default = False, index = True)
    completed     = Column(Boolean, default = False, index = True)
    compensated   = Column(Boolean, default = False, index = True)
    accepted      = Column(Boolean, default = False, index = True)
    validated     = Column(Boolean, default = False, index = True)
    useful        = Column(Boolean, default = True)


    def publish(self):
        if self.published:
            raise RuntimeError("HIT cannot be published because it has already"
                " been published.")
        # resp = api.server.createhit(
        #     title = self.group.title,
        #     description = self.group.description,
        #     amount = self.group.cost,
        #     duration = self.group.duration,
        #     lifetime = self.group.lifetime,
        #     keywords = self.group.keywords,
        #     height = self.group.height,
        #     minapprovedamount = self.group.minapprovedamount,
        #     minapprovedpercent = self.group.minapprovedpercent,
        #     countrycode = self.group.countrycode,
        #     page = self.getpage())

        resp = api.server.createhit(
            title = 'title',
            description = 'description',
            amount = None,
            duration = None,
            lifetime = None,
            page = self.getpage())
        self.hitid = resp.hitid
        self.published = True
        logger.debug("Published HIT {0}".format(self.hitid))

    ## TODO get page
    def getpage(self):
        page= '/index.html'
        return "{0}?id={1}".format(page, self.id)

    def markastraining(self):
        """
        Marks this job as the result of a training run. This will automatically
        swap this job over to the training video and produce a replacement.
        """
        replacement = Job(segment = self.segment, group = self.group)
        self.segment = self.segment.video.trainwith.segments[0]
        self.group = self.segment.jobs[0].group
        self.istraining = True

        logger.debug("Job is now training and replacement built")

        return replacement

    def invalidate(self):
        """
        Invalidates this path because it is poor work. The new job will be
        respawned automatically for different workers to complete.
        """
        self.useful = False
        # is this a training task? if yes, we don't want to respawn
        if not self.istraining:
            return Job(segment = self.segment, group = self.group)

    def check(self):
        if len(self.paths) > config.maxobjects:
            raise RuntimeError("Job {0} has too many objects to process "
                               "payment. Please verify this is not an "
                               "attempt to hack us and increase the "
                               "limit in config.py".format(self.id))
        return True

    def offlineurl(self, localhost):
        return "{0}{1}&hitId=offline".format(localhost, self.getpage())

    @property
    def trainingjob(self):
        return self.segment.video.trainwith.segments[0].jobs[0]

    @property
    def cost(self): 
        if not self.completed:
            return 0
        return self.bonusamount + self.group.cost + self.donatedamount

    def __iter__(self):
        return self.paths

class Path(Model, CRUDMixin):
    __tablename__ = "paths"
    
    id = Column(Integer, primary_key = True)
    jobid = Column(Integer, ForeignKey(Job.id))
    job = relationship(Job, backref = backref("paths", cascade="all,delete"))
    labelid = Column(Integer, ForeignKey(Label.id))
    label = relationship(Label, cascade = "none", backref = "paths")
    userid = Column(Integer, default=0)
    done = Column(Boolean, default = False)

    interpolatecache = None

    def getboxes(self, interpolate = False, bind = False, label = False, groundplane = False):
        result = [x.getbox() for x in self.boxes]
        result.sort(key = lambda x: x.frame)

        if groundplane:
            homography = None
            with open(os.path.join(
                    self.job.segment.video.homographylocation,
                    "homography.npy"
                ), "r") as f:
                homography = np.load(f)

            for i in range(len(result)):
                t = homography.dot(np.array([result[i].xbr, result[i].ybr, 1]))
                result[i].xbr = float(t[0]) / t[2]
                result[i].ybr = float(t[1]) / t[2]
                result[i].xtl = result[i].xbr - 5
                result[i].ytl = result[i].ybr - 5

        if interpolate:
            if not self.interpolatecache:
                self.interpolatecache = LinearFill(result)
            result = self.interpolatecache

        if bind:
            result = Path.bindattributes(self.attributes, result)

        if label:
            for box in result:
                box.attributes.insert(0, self.label.text)

        return result

    @classmethod 
    def bindattributes(cls, attributes, boxes):
        attributes = sorted(attributes, key = lambda x: x.frame)

        byid = {}
        for attribute in attributes:
            if attribute.attributeid not in byid:
                byid[attribute.attributeid] = []
            byid[attribute.attributeid].append(attribute)

        for attributes in byid.values():
            for prev, cur in zip(attributes, attributes[1:]):
                if prev.value:
                    for box in boxes:
                        if prev.frame <= box.frame < cur.frame:
                            if prev.attribute not in box.attributes:
                                box.attributes.append(prev.attribute)
            last = attributes[-1]
            if last.value:
                for box in boxes:
                    if last.frame <= box.frame:
                        if last.attribute not in box.attributes:
                            box.attributes.append(last.attribute)

        return boxes

    def __repr__(self):
        return "<Path {0}>".format(self.id)

class AttributeAnnotation(Model, CRUDMixin):
    __tablename__ = "attribute_annotations"

    id = Column(Integer, primary_key = True)
    pathid = Column(Integer, ForeignKey(Path.id))
    path = relationship(Path,
                        backref = backref("attributes",
                                          cascade = "all,delete"))
    attributeid = Column(Integer, ForeignKey(Attribute.id))
    attribute = relationship(Attribute)
    frame = Column(Integer)
    value = Column(Boolean, default = False)

    def __repr__(self):
        return ("AttributeAnnotation(pathid = {0}, "
                                    "attributeid = {1}, "
                                    "frame = {2}, "
                                    "value = {3})").format(self.pathid,
                                                           self.attributeid,
                                                           self.frame,
                                                           self.value)

class Box(Model, CRUDMixin):
    __tablename__ = "boxes"

    id = Column(Integer, primary_key = True)
    pathid = Column(Integer, ForeignKey(Path.id))
    path = relationship(Path,
                        backref = backref("boxes", cascade = "all,delete"))
    xtl = Column(Integer)
    ytl = Column(Integer)
    xbr = Column(Integer)
    ybr = Column(Integer)
    frame = Column(Integer)
    occluded = Column(Boolean, default = False)
    outside = Column(Boolean, default = False)
    generated = Column(Boolean, default = False)

    def frombox(self, box):
        self.xtl = box.xtl
        self.xbr = box.xbr
        self.ytl = box.ytl
        self.ybr = box.ybr
        self.frame = box.frame
        self.occluded = box.occluded
        self.outside = box.lost
        self.generated = box.generated

    def getbox(self):
        vb=vision.Box(self.xtl, self.ytl, self.xbr, self.ybr,
                      self.frame, self.outside, self.occluded,
                      0, generated=self.generated)
#        print 'frame id: {}, generated: {}'.format(vb.frame, vb.generated)
        return vb

