#!/bin/sh
#

cd /home/admin/dns
sudo ./createZone.py --user admin
sudo rndc reload
