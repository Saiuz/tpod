import cv2

from db_util import session
from models import *


def extract(path_video, path_output):
    if not os.path.isdir(path_output):
        os.makedirs(path_output)
    if not os.path.isfile(path_video):
        return False
    cap = cv2.VideoCapture(path_video)
    count = 0
    success, image = cap.read()
    while success:
        img_path = Video.getframepath(count, path_output)
        if not os.path.isdir(os.path.dirname(img_path)):
            os.makedirs(os.path.dirname(img_path))
        cv2.imwrite(img_path, image)
        success, image = cap.read()
        count += 1
    return True


def load(video_name, video_path_output, labels):
    # video_name = slug
    # video_path_output = location
    first_frame_path = Video.getframepath(0, video_path_output)
    first_frame = image_exist(first_frame_path)
    if first_frame is None:
        return False
    width = first_frame.shape[1]
    height = first_frame.shape[0]

     # search for last frame
    toplevel = max(int(x)
        for x in os.listdir(video_path_output))
    secondlevel = max(int(x)
        for x in os.listdir("{0}/{1}".format(video_path_output, toplevel)))
    maxframes = max(int(os.path.splitext(x)[0])
        for x in os.listdir("{0}/{1}/{2}"
        .format(video_path_output, toplevel, secondlevel))) + 1

    print "Found {0} frames.".format(maxframes)
    last_frame_path = Video.getframepath(maxframes - 1, video_path_output)
    last_frame = image_exist(last_frame_path)
    if last_frame is None:
        return False
    query = session.query(Video).filter(Video.slug == video_name)
    if query.count() > 0:
        print "Video {0} already exists!".format(video_name)
        print "updating labels for {0}".format(video_name)
        # j: add in update label function
        video=session.query(Video).filter(Video.slug == video_name).first()
        # check if such label has any paths associated with it
        for label in video.labels:
            if not session.query(Path).filter(Path.labelid == label.id).count():
                print 'No path associated. deleted label {} {}'.format(label.id, label.text)
                session.delete(label)
            else:
                print 'Path associated exists. keep label {} {}'.format(label.id, label.text)
        existing_labels = [label.text for label in video.labels]
        labelcache = {}
        attributecache = {}
        lastlabel = None
        for labeltext in labels:
            if labeltext[0] == "~":
                if lastlabel is None:
                    print "Cannot assign an attribute without a label!"
                    return
                labeltext = labeltext[1:]
                attribute = Attribute(text = labeltext)
                session.add(attribute)
                lastlabel.attributes.append(attribute)
                attributecache[labeltext] = attribute
            else:
                if labeltext in existing_labels:
                    print 'label: {} already in video'.format(label)
                    continue
                label = Label(text = labeltext)
                print 'add label: {}'.format(label)
                session.add(label)
                video.labels.append(label)
                labelcache[labeltext] = label
                lastlabel = label
        session.commit()
        return
    homographydir = os.path.abspath(os.path.join("homographies", video_name))
    if not os.path.isdir(homographydir):
        os.makedirs(homographydir)
    np.save(os.path.join(homographydir, "homography.npy"), np.identity(3))

    # create video
    video = Video(slug = video_name,
                  location = os.path.realpath(video_path_output),
                  width = width,
                  height = height,
                  totalframes = maxframes,
                  skip = 0,
                  perobjectbonus = 0,
                  completionbonus = 0,
                  trainwith = None,
                  isfortraining = False,
                  blowradius = 0,
                  homographylocation = homographydir,
                  pointmode = False)
    session.add(video)
    print "Binding labels and attributes..."

    # create labels and attributes
    labelcache = {}
    attributecache = {}
    lastlabel = None
    for labeltext in labels:
        if labeltext[0] == "~":
            if lastlabel is None:
                print "Cannot assign an attribute without a label!"
                return
            labeltext = labeltext[1:]
            attribute = Attribute(text = labeltext)
            session.add(attribute)
            lastlabel.attributes.append(attribute)
            attributecache[labeltext] = attribute
        else:
            label = Label(text = labeltext)
            print 'add label: {}'.format(label)
            session.add(label)
            video.labels.append(label)
            labelcache[labeltext] = label
            lastlabel = label

    print "Creating symbolic link..."
    symlink = "public/frames/{0}".format(video.slug)
    try:
        os.remove(symlink)
    except:
        pass
    os.symlink(video.location, symlink)

    print "Creating segments..."
    # create shots and jobs
    startframe = 0
    stopframe =  video.totalframes - 1
    length = 1000
    for start in range(startframe, stopframe, length):
        stop = min(start + length + 1,
                   stopframe)
        segment = Segment(start = start,
                            stop = stop,
                            video = video)
        job = Job(segment = segment)
        session.add(segment)
        session.add(job)
    session.commit()






def image_exist(img_path):
    try:
        img = cv2.imread(img_path)
        return img
    except Exception:
        print "Image not exist " + str(img_path)
    return None


