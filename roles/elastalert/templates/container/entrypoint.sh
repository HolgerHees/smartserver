#!/bin/sh

/usr/bin/elastalert --verbose --rule /etc/elastalert/rule.yaml --config /etc/elastalert/config.yaml 2>&1
