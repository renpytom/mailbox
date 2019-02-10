#!/bin/bash

scp blescan.py root@laika:/root
ssh -t root@laika sudo /root/.virtualenvs/ble/bin/python3 /root/blescan.py

