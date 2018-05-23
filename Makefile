# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

include .env

.DEFAULT_GOAL=build

network:
	@docker network inspect $(DOCKER_NETWORK_NAME) >/dev/null 2>&1 || docker network create $(DOCKER_NETWORK_NAME)

volumes:
	@docker volume inspect $(DATA_VOLUME_HOST) >/dev/null 2>&1 || docker volume create --name $(DATA_VOLUME_HOST)

self-signed-cert:
	# make a self-signed cert

secrets/oauth.env:
	@echo "Need oauth.env file in secrets with GitHub parameters"
	@exit 1

userlist:
	@echo "Add usernames, one per line, to ./jupyterhub-data/userlist, such as:"
	@echo "    zoe admin"
	@echo "    wash"
	@exit 1


check-files: jupyterhub-data/userlist secrets/oauth.env

pull:
	docker pull $(DOCKER_NOTEBOOK_IMAGE)

notebook_image: pull singleuser/Dockerfile
	docker build -t $(LOCAL_NOTEBOOK_IMAGE) \
		--build-arg JUPYTERHUB_VERSION=$(JUPYTERHUB_VERSION) \
		--build-arg DOCKER_NOTEBOOK_IMAGE=$(DOCKER_NOTEBOOK_IMAGE) \
		singleuser

build: check-files network volumes
	docker-compose build

.PHONY: network volumes check-files pull notebook_image build
