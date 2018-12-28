#!/bin/bash

DOCKER_USER=hwwwi
DOCKER_IMAGE=python-chromedriver
DOCKER_TAG=python3-selenium-3.8.0

docker build -t \
  ${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_TAG} \
	-f ./Dockerfile .
