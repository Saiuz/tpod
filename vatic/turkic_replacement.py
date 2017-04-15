import cv2

from models import *
from tpod_models import *
import shutil
import db_util


def delete_video(video_id):
    session = db_util.renew_session()
    video = session.query(Video).filter(Video.id == video_id).first()
    if video:
        # delete original file
        original_file_path = video.orig_file_path
        if os.path.exists(original_file_path):
            os.remove(original_file_path)

        # delete extract file
        extract_file_path = video.extract_path
        if os.path.exists(extract_file_path):
            shutil.rmtree(extract_file_path)

        # delete frame folder
        frame_folder_path = 'public/frames/' + str(video.slug)
        try:
            shutil.rmtree(frame_folder_path)
        except:
            logger.debug('remove video frame unsuccess')
        try:
            os.remove(frame_folder_path)
        except:
            logger.debug('remove video frame unsuccess')
        try:
            os.unlink(frame_folder_path)
        except:
            logger.debug('remove video frame unsuccess')
        try:
            os.rmdir(frame_folder_path)
        except:
            logger.debug('remove video frame unsuccess')

        # delete labels
        labels = session.query(Label).filter(Label.videoid == video_id).all()
        for label in labels:
            # delete label related path
            paths = session.query(Path).filter(Path.labelid == label.id).all()
            for path in paths:
                session.delete(path)
            session.delete(label)

        # delete segments
        segments = session.query(Segment).filter(Segment.videoid == video_id).all()
        for segment in segments:
            # delete session related job
            jobs = session.query(Job).filter(Job.segmentid == segment.id).all()
            for job in jobs:
                session.delete(job)
            session.delete(segment)
        session.delete(video)
        session.commit()
        session.close()
        return True
    session.close()
    return False


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
        # resize the image to 720 x 480
        hw_ratio = float(image.shape[0])/float(image.shape[1])
        if hw_ratio > 480.0 / 720.0:
            target_height = 480
            target_width = target_height/hw_ratio
        else:
            target_width = 720
            target_height = target_width * hw_ratio
        image = cv2.resize(image, (int(target_width), int(target_height)))
        cv2.imwrite(img_path, image)
        success, image = cap.read()
        count += 1
    return True


def extract_image_sequences(image_path_list, path_output):
    if not os.path.isdir(path_output):
        os.makedirs(path_output)

    count = 0
    for path in image_path_list:
        img_path = Video.getframepath(count, path_output)
        image = cv2.imread(path)
        if image is None:
            continue
        if not os.path.isdir(os.path.dirname(img_path)):
            os.makedirs(os.path.dirname(img_path))
        # resize the image to 720 x 480
        hw_ratio = float(image.shape[0])/float(image.shape[1])
        if hw_ratio > 480.0 / 720.0:
            target_height = 480
            target_width = target_height/hw_ratio
        else:
            target_width = 720
            target_height = target_width * hw_ratio
        image = cv2.resize(image, (int(target_width), int(target_height)))
        cv2.imwrite(img_path, image)
        count += 1
    return True


def load(video_name, video_path_output, labels, orig_file_path, user_id, segment_length = 3000):
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
    session = db_util.renew_session()
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

    current_user = session.query(User).filter(User.id == user_id).first()

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
                  pointmode = False,
                  orig_file_path = orig_file_path,
                  extract_path = video_path_output,
                  owner_id=user_id)
    session.add(video)
    current_user.videos.append(video)

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
    if not os.path.exists('public/frames'):
        os.makedirs('public/frames')
    os.symlink(video.location, symlink)

    print "Creating segments..."
    # create shots and jobs
    startframe = 0
    stopframe =  video.totalframes - 1
    for start in range(startframe, stopframe, segment_length):
        stop = min(start + segment_length + 1,
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


def publish():
    return None
    # try:
    #     query = session.query(Job)
    #     query = query.filter(Job.ready == True)
    #     query = query.filter(Job.published == False)
    #     for hit in query:
    #         hit.publish()
    #         print hit.offlineurl(config.localhost)
    #         print "Published {0}".format(hit.hitid)
    #         session.add(hit)
    #         session.commit()
    # except Exception as e:
    #     print e
    # finally:
    #     session.commit()
    #     session.close()


    # try:
    #     query = session.query(HIT)
    #     query = query.join(HITGroup)
    #     query = query.filter(HITGroup.offline == args.offline)
    #     query = query.filter(HIT.ready == True)
    #     query = query.filter(HIT.published == False)
    #     for hit in query:
    #         if args.offline:
    #             print hit.offlineurl(config.localhost)
    #         else:
    #             hit.publish()
    #             print "Published {0}".format(hit.hitid)
    #             session.add(hit)
    #             session.commit()
    # finally:
    #     session.commit()
    #     session.close()



