# TPOD (A Tool for Painless Object Detection)
-----------------

TPOD, a tool for painless object detection, is a web-based system that simplifies and streamlines the process of creating DNN-based highly accurate object detectors. It helps application developers with no prior computer vision background to quickly collect training images, label them, and train object detector. 

TPOD is your one stop shop for instance object detection. 


## Usage

1. Record multiple videos of ~30 seconds capturing the object you want to create an object detector for. Videos capturing the object under different view points, lighting conditions, scale, and with negative examples in your use case work better.
2. Upload the videos to TPOD on the video management page.
3. Add labels, specifying the name of the object for each video.
4. Go to classifier management, select training videos, and launch training.
5. When the training is finsihed, you can upload sample test images to get a feeling on how well the classifier is working by going to the "detection" column in the classifier management page.
6. Export the container image to integrate it with your own application

(An old instructional video is [here](https://youtu.be/S-zovh8yUcQ). The overall workflow stayed the same.)

## Installation

We provide an installation script install.sh for ubuntu 14.04 and 16.04. Current TPOD backend can only run on a machine with a GPU.

1. 
```
git clone https://github.com/junjuew/TPOD.git
cd TPOD
```
2. Copy env-template.sh into env.sh. Customize your configuration. TPOD will create an admin user specified by DEFAULT_USER and DEFAULT_USER_PASSWORD. You'll need this username and password to login. CONTAINER_REGISTRY_URL should be a docker container registry. It is where the trained object detector image will be pushed into.
```
cp env-template.sh env.sh
```
3. Pull the faster-rcnn container base image. TPOD uses the base image to fine-tune the faster-rcnn object detection model.
```
docker pull registry.cmusatyalab.org/junjuew/container-registry:faster-rcnn-primitive
```
4. Run the installation script. It only supports ubuntu right now. The installation script installs system packages including mysql, opencv and rabbitmq. The python dependencies are installed into a virtualenv named "env" under current directory.
```
./install.sh
```
5. To run, copy and customize run-template.sh into run.sh. TPOD is listening on port 10000 by default.
```
cp run-template.sh run.sh
./run.sh
```

## Usage of generated TPOD container image

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

## Sample Training Dataset
There are 3 files needed for the training: image_list, label_list, label_name; They are all stored under folder 'dataset', and it's shared to all docker containers through data volume
* Image_list: this contains the list of file path for all images, each line represent one frame
* Label_list: this contains the actual bounding box for labels in each frame, each line represent the label for one frame, and it's organized in three levels:
    * Classes are separated by dot '.'
    * Bounding boxes under that class are separated by semicolon ';'
    * Coordinates for the box (since there are two x, two y for each box) are separated by comma ';'
Thus here is a sample for the label for one frame, it contains two classes (we call them 'A' and 'B'), which have 2 and 3 boxes (we call them 'A1', 'A2', 'B1', 'B2', 'B3') respectively, and they have coordinates (x, y, w, h):
* A1: [101, 201, 10, 20] 
* A2: [102, 202, 10, 20]
* B1: [103, 203, 10, 20]
* B2: [104, 204, 10, 20]
* B3: [105, 205, 10, 20]

Then the label for that frame looks like this 
>> 101,201,10,20;102,202,10,20.103,203,10,20;104,204,10,20;105,205,10,20


# Q & A
=========================

## What if I want to change the database model? 
1. Make the change
2. (Under the tpod root folder) python app.py db migrate 
3. (Under the tpod root folder) python app.py db upgrade

# Licensing
Unless otherwise stated, the source code are copyright Carnegie Mellon University and licensed under the [Apache 2.0 License](./LICENSE).
Portions from the following third party sources have been modified and are included in this repository.
These portions are noted in the source files and are copyright their respective authors with the licenses listed.

Project | Modified | License
---|---|---|
[cvondrick/vatic](https://github.com/cvondrick/vatic) | Yes | MIT
