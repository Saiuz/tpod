#!/bin/bash -ex
#
# Copyright 2018 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

echo "start installing system wide packages including python, opencv, and mysql"
sudo apt-get install python-setuptools python-dev python-virtualenv libavcodec-dev libavformat-dev libav-tools libswscale-dev libjpeg62 libfreetype6 libfreetype6-dev libopencv-dev python-opencv mysql-server mysql-client libmysqlclient-dev gfortran rabbitmq-server cmake libboost-all-dev build-essential

sudo easy_install pip
sudo pip install -U pip

echo "start installing requiements into virtualenv env"
virtualenv --system-site-packages env # use system-site opencv package
. env/bin/activate

# these are dependencies for packages built from git
# pip 2 pass installation doesn't work well
pip install -U pip
pip install cython==0.20
pip install numpy==1.12.1
pip install -r requirements.txt

source env.sh

echo "setting up mysql database"
echo "Please enter root user MySQL password!"
read -s -p "Password:" rootpasswd
mysql -uroot -p${rootpasswd} -e "CREATE DATABASE ${DB_NAME};" || true
mysql -uroot -p${rootpasswd} -e "CREATE USER ${DB_USER}@localhost IDENTIFIED BY '${DB_PASSWORD}';" || true
mysql -uroot -p${rootpasswd} -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';" || true
mysql -uroot -p${rootpasswd} -e "FLUSH PRIVILEGES;" || true
echo "success"
