#!/bin/bash

SELENIUM_IMAGE="hwwwi/python-chromedriver:python3-selenium-3.8.0"

docker run -it \
  --user=$(id -u):$(id -g) \
  -e USER=$(id -u) \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  -v /etc/localtime:/etc/localtime:ro \
  -v $(pwd):/usr/workspace \
  ${SELENIUM_IMAGE} \
  sh -c "python /usr/workspace/app.py"
