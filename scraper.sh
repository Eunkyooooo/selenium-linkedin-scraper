#!/bin/bash

SELENIUM_IMAGE="hwwwi/python-chromedriver:python3-selenium-3.8.0"

# Mounting /dev/shm will fix chorme crash error
# https://github.com/elgalu/docker-selenium/issues/20

docker run --rm -it \
  --user=$(id -u):$(id -g) \
  -e USER=$(id -u) \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  -v /etc/localtime:/etc/localtime:ro \
  -v $(pwd):/usr/workspace \
  -v /dev/shm:/dev/shm \
  -w /usr/workspace \
  ${SELENIUM_IMAGE} \
  sh -c "python /usr/workspace/app.py"
