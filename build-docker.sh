#!/bin/bash

DOCKER_CMD=docker

if ! command -v docker &> /dev/null
then
    if ! command -v podman &> /dev/null
    then
        echo "Install docker or podman"
        exit
    fi
    DOCKER_CMD=podman
fi

$DOCKER_CMD build -t exchange_api .
