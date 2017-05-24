## TPOD

## To start celery
* ./runcelery.py -A celery_tasks worker --loglevel=debug

-----------------
### Dependencies

#### Install OpenCV
* sudo apt-get install build-essential
* sudo apt-get install cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
* sudo apt-get install python-dev python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev
* git clone https://github.com/Itseez/opencv_contrib.git
* checkout Version: 2.4.13
* mkdir build
* cd build
* cmake -D CMAKE_BUILD_TYPE=RELEASE \
*     -D CMAKE_INSTALL_PREFIX=/usr/local \
*     -D INSTALL_C_EXAMPLES=ON \
*     -D INSTALL_PYTHON_EXAMPLES=ON \
*     -D BUILD_EXAMPLES=ON ..
* make -j16
* sudo make install


Reference: http://docs.opencv.org/2.4/doc/tutorials/introduction/linux_install/linux_install.html


#### Install Vatic
* sudo apt-get install python-setuptools python-dev libavcodec-dev libavformat-dev libswscale-dev libjpeg62 libjpeg62-dev libfreetype6 libfreetype6-dev mysql-server-5.5 mysql-client-5.5 libmysqlclient-dev gfortran

* mysql> CREATE USER ‘vatic'@'localhost' IDENTIFIED BY ‘vatic';
* be sure to execute db_util.install() in python under the project root folder first, this will initialize all database models related with tpod
    * python
    * \>> import db_util
    * \>> db_util.install()


#### Requirement:
all requirement is in the file: requirement.txt under tpod root folder


#### Sample Training Dataset
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

    nvidia-docker run -it -p 0.0.0.0:8000:8000 --rm --name <container-name> <container-image> /bin/bash run_server.sh

Send http request:

     http --form post http://cloudlet015.elijah.cs.cmu.edu:8000/detect picture@appleGreen.jpg confidence=0.95 format=box


format: 
1. http form binary file
2. keywords:
   1. confidence 
   2. format: "box" or "image"