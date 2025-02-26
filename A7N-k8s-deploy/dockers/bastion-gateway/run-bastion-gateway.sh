#!/bin/bash
docker buildx create --name mybuilder --use

docker buildx build --platform linux/amd64,linux/arm64 -t warlockee/bastion-gw:latest --push .