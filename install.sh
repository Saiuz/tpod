#!/bin/bash -ex

echo "start installing system wide packages including python, opencv, and mysql"
sudo apt-get install python-setuptools python-dev python-pip libavcodec-dev libavformat-dev libswscale-dev libjpeg62 libfreetype6 libfreetype6-dev libopencv-dev python-opencv mysql-server-5.5 mysql-client-5.5 libmysqlclient-dev gfortran

echo "start installing requiements into virtualenv env"
virtualenv env
. env/bin/activate

# these are dependencies for packages built from git
# pip 2 pass installation doesn't work well
pip install cython==0.20
pip install numpy==1.12.1
pip install -r requirements.txt
