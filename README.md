# TPOD (A Tool for Painless Object Detection)

TPOD, a tool for painless object detection, is a web-based system that simplifies and streamlines the process of creating DNN-based highly accurate object detectors. It helps application developers with no prior computer vision background to quickly collect training images, label them, and train object detector. 

TPOD is your one stop shop for object detection. 



# Q & A
=========================



## What if I want to change the database model? 
1. Make the change
2. (Under the tpod root folder) python app.py db migrate 
3. (Under the tpod root folder) python app.py db upgrade


## How to export labeled videos and import videos from other platform?

Good question, we support that!

1. Ensure that you are using our tools on either TPOD (through our web interface) or on cloudlet 001 through commandline
2. Ensure that you have completely labeled the video

Export on TPOD:
* There is a 'Export Video' button on video management page (on the very right column of that page)
* You can click on that button, then you will get a zip ball, it contains all images and annotations for that video, and it's in PASCAL format

Import on TPOD:
* If you are using TPOD or our commandline tool (export.py, will be explained later), you will get a zip ball, just upload that zip ball on the video upload interface, and check the checkbox to indicate that it's a labeled sample 
* After uploading the labeled zip ball, there should be a labaled video on the web page
* There are several things to mention about that video. First, it will not be resized, thus it's in the original size as those in your zip ball; 2. there will be no tracking related with each annotation (in TPOD of vatic, there exist a tracking mechanism, which only record critical frames, thus greatly reduce the box records), this might brings in an issue, since each frame contains actual label, the frontend might takes a while to load these labels, then on Vatic labeling page, you will have to wait longer before it's loaded 

Export through commandline
* On cloudlet001, there is a 'export_label.py' under folder '/home/suanmiao/workspace/tpod_export', you can use that file to export labeled file, the result is the same as that from TPOD
* First, you have to ensure that the virtual environment (under folder '/home/junjuew/object-detection-web/demo-web/flask') is activated
* Second, ensure that other python files under my folder ('/home/suanmiao/workspace/tpod_export') is also under you execution dir, thus you can directly copy all files under that folder to your working dir and execute it, it should ensure the correctness
* There are two parameters 'video' and 'target_folder'. 'video' is the actual video name for the video stored in DB, thus it will depend on the actual implementation, under Junjue's TPOD, the name should be userid_videoname, for example '3_dummy_video_1.mp4', the result will be stored in the target folder, more instructions will be displayed during your execution


### Usage of generated TPOD container image

#### Running as a standalone HTTP server

    nvidia-docker run -it -p 0.0.0.0:8000:8000 --rm \
    --name <container-name> <container-image> /bin/bash run_server.sh

HTTP Request Format: 
1. The image to be detected should be a file in http form
2. Other HTTP form keywords:
   1. 'confidence': a number between 0 to 1. The minimum confidence score for bounding boxes outputted
   2. 'format': "box" or "image". The format of output

Sample Request Format (using httpie):

    http --form post http://cloudlet015.elijah.cs.cmu.edu:8000/detect \
    picture@appleGreen.jpg confidence=0.95 format=box

#### Running as a detection script

     nvidia-docker run -it -v <host-dir>:<container-dir> --rm \
     --name <container-name> <container-image> tools/tpod_detect_cli.py \
     --input_image <input-image-path> --min_cf <confidence score> --output_image <output-image-path>

The --output_image is optional. If omitted, the detected bounding boxes will be printed to stdout in json format. If specified, the output will be an image with bounding boxes. <input-image-path> and <output-image-path> should be inside directories accessiable by both host and containers as specified in -v option. 

Example:

     nvidia-docker run -it -v /tmp:/tmp --rm \
     --name detection_container apple_detector_container_image tools/tpod_detect_cli.py \
     --input_image /tmp/test.jpg --min_cf 0.5 --output_image /tmp/result.jpg

#### Container Image Content

* Caffe prototxt file is at: /py-faster-rcnn/assembled_end2end/faster_rcnn_test.pt
* Model files are stored at: '/py-faster-rcnn/model_iter_(iteration-number).caffemodel'. The one with the largest iteration number usually should be used for detection.
* Label file is at: '/train/labels.txt'
* Training Image Set file is at: '/train/image_set.txt'
* Training Annotation file is at: '/train/label_set.txt'
