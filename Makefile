MINOR_REV_FILE=build-revision.txt
MAJOR_REV_FILE=major-revision.txt

.PHONY: perfctl

push:
	@if ! test -f $(MINOR_REV_FILE); then echo 0 > $(MINOR_REV_FILE); fi
	@echo $$(($$(cat $(MINOR_REV_FILE)) + 1)) > $(MINOR_REV_FILE)
	@if ! test -f $(MAJOR_REV_FILE); then echo 1 > $(MAJOR_REV_FILE); fi
	$(eval MAJOR_REV := $(shell cat $(MAJOR_REV_FILE)))
	$(eval MINOR_REV := $(shell cat $(MINOR_REV_FILE)))
	docker build --force-rm=true --no-cache=true -t perfctl -f Dockerfile .
	docker image tag perfctl:latest mminichino/perfctl:latest
	docker image tag perfctl:latest mminichino/perfctl:$(MAJOR_REV).0.$(MINOR_REV)
	docker push mminichino/perfctl:latest
	docker push mminichino/perfctl:$(MAJOR_REV).0.$(MINOR_REV)
build:
	docker build --force-rm=true --no-cache=true -t perfctl -f Dockerfile .
