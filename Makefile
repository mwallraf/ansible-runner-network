PYTHON ?= python3

CONTAINER_ENGINE ?= docker

NAME = ansible-runner
IMAGE_NAME ?= ansible-runner-network
#GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
GIT_BRANCH = 1.0
ANSIBLE_RUN_SCRIPT_LINK=ansible-run
ANSIBLE_RUN_SCRIPT=ansible-run.sh
ANSIBLE_VAULT_IDENTITY=ansible_plugins/vault/.vault
PROJECT_ACCESS_GROUP=staff

DEMO_PROJECT = ansible_plugins/_scaffold_
PROJECT ?= demo
PLAYBOOK ?= playbook

.PHONY: clean symlink init init_permissions build project run shell

clean:
	rm -rf /usr/local/bin/${ANSIBLE_RUN_SCRIPT_LINK}
	rm -rf projects/${PROJECT}

init_permissions:
	chgrp -R ${PROJECT_ACCESS_GROUP} $(shell pwd)
	chmod 600 ${ANSIBLE_VAULT_IDENTITY}
	chmod 770 projects
	chmod 750 ${ANSIBLE_RUN_SCRIPT}
	chmod -R 750 projects/demo

# initialize folder permissions
init: clean symlink project init_permissions build
	

symlink:
	ln -s $(shell pwd)/${ANSIBLE_RUN_SCRIPT} /usr/local/bin/${ANSIBLE_RUN_SCRIPT_LINK}

# build the docker container
build:
	$(CONTAINER_ENGINE) build --rm=true \
		-t $(IMAGE_NAME) -f Dockerfile .
	$(CONTAINER_ENGINE) tag $(IMAGE_NAME) $(IMAGE_NAME):$(GIT_BRANCH)


# create a new project based on demo project
# usage: make project PROJECT=your_project_name
project:
	cp -R ${DEMO_PROJECT} projects/${PROJECT}
	chmod -R 770 projects/${PROJECT}


# run the project
# usage: make run PROJECT=your_project_name [PLAYBOOK=playbook]
run:
	docker run --rm \
	    -e RUNNER_PROJECT=${PROJECT} \
	    -e RUNNER_PLAYBOOK=${PLAYBOOK}.yml \
		-v $(shell pwd)/projects/${PROJECT}:/runner \
		$(IMAGE_NAME):$(GIT_BRANCH)


# open a commandline shell into docker for the project
# usage: make shell PROJECT=your_project_name [PLAYBOOK=playbook]
# manually running the playbook: ansible-runner run /runner
shell:   
	docker run --rm -ti \
	    -e RUNNER_PROJECT=${PROJECT} \
	    -e RUNNER_PLAYBOOK=${PLAYBOOK}.yml \
		-v $(shell pwd)/projects/${PROJECT}:/runner \
		$(IMAGE_NAME):$(GIT_BRANCH) \
		/bin/bash
