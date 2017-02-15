#!/bin/sh
hciattach -t 20 /dev/ttyAMA0 bcm43xx 921600 noflow -
hciattach  /dev/ttyAMA0 bcm43xx 921600 noflow -
hciconfig hci0 up
while true; do sleep 60; done
