## TPOD

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



















