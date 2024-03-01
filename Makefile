DS ?= swing_1
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

ifneq ("$(wildcard .env)","")
	include .env
endif

define HEADER
Run and test pre-builder locally from remote repository of Dilla ds under https://gitlab.com/dilla-io/ds.

Variables, ex: `DS=material_2 make test`
 - DS:	Design system to use for [Run] commands, default 'swing_1'

endef
export HEADER

help:
	@echo "$$HEADER"
	@sed \
		-e '/^[a-zA-Z0-9_\-]*:.*##/!d' \
		-e 's/:.*##\s*/:/' \
		-e 's/^\(.\+\):\(.*\)/$(shell tput setaf 6)\1$(shell tput sgr0):\2/' \
		$(MAKEFILE_LIST) | column -c2 -t -s :

test: build ## Test prebuilder on a design system, `DS=swing_1 make test`, download the DS from gitlab.com/dilla-io/ds
ifndef GITLAB_TOKEN
	$(error [ERROR] GITLAB_TOKEN is undefined, please fill .env file or set environment variable)
endif
	@mkdir -p $(DS)_output
	@curl -sL --header "Private-Token: ${GITLAB_TOKEN}" https://gitlab.com/dilla-io/ds/$(DS)/-/archive/master/$(DS)-master.tar.gz | tar -xz
	@docker run -t -v $(ROOT_DIR)/$(DS)-master:/data/input -v $(ROOT_DIR)/$(DS)_output:/data/output prebuilder build
	@docker run -t -v $(ROOT_DIR)/$(DS)-master:/data/input -v $(ROOT_DIR)/$(DS)_output:/data/output:rw prebuilder data

run: ## Run prebuilder on a local input as $DS-master and output to $DS_output, `DS=swing_1 make run`
	docker run -t -v $(ROOT_DIR)/$(DS)-master:/data/input -v $(ROOT_DIR)/$(DS)_output:/data/output prebuilder run

build: ## Build prebuilder Docker image
	 docker build -t prebuilder --rm .

lint: ## Lint prebuilder code
	- prettier --write README.md
	- ruff check *.py
	- ruff format *.py
	- mypy --strict *.py
	- radon cc *.py -nc -s
	- flake8 --select D102 *.py
