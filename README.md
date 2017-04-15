## TPOD

-----------------
### Dependencies

Install OpenCV
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


http://docs.opencv.org/2.4/doc/tutorials/introduction/linux_install/linux_install.html


Install Vatic
* sudo apt-get install python-setuptools python-dev libavcodec-dev libavformat-dev libswscale-dev libjpeg62 libjpeg62-dev libfreetype6 libfreetype6-dev mysql-server-5.5 mysql-client-5.5 libmysqlclient-dev gfortran

* mysql> CREATE USER ‘vatic'@'localhost' IDENTIFIED BY ‘vatic';


Pip install
SQLAlchemy
wsgilog
cython==0.20
mysql-python
munkres
parsedatetime
argparse
numpy
Pillow
dlib
* sudo apt-get install libboost-all-dev
* pip install dlib
* 
flask
simplejson


# Q & A
=========================



## What if I want to change the database model? 
1. Make the change
2. (Under the tpod root folder) python app.py db migrate 



















