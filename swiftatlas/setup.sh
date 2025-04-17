#!/bin/sh -e

pip install -r requirements.txt

if [ ! -e "logs" ]; then
  mkdir logs
fi
