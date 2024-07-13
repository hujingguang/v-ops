#!/bin/bash - 
#===============================================================================
#
#          FILE: init.sh
# 
#         USAGE: ./init.sh 
# 
#   DESCRIPTION: 初始化运行环境
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: hoover.hu
#  ORGANIZATION: 
#       CREATED: 11/03/2020 16:06
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error

yum remove mariadb-libs -y
yum install mysql-devel gcc gcc-devel python-devel zlib-devel zlib openssl openssl-devel make cmake  openldap-devel git -y
pip3 install -r ./requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ 
