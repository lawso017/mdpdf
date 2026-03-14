.PHONY: test test-integration test-all build push install pull

IMAGE := ghcr.io/lawso017/mdpdf:latest

test: ## Run unit tests (no Docker needed)
	uv run pytest tests/ -v --ignore=tests/test_integration.py

test-integration: ## Run integration tests (requires Docker)
	docker run --rm \
		-v $(PWD)/tests:/opt/mdpdf/tests \
		--entrypoint uv \
		$(IMAGE) \
		run --project /opt/mdpdf pytest /opt/mdpdf/tests/test_integration.py -v -m integration

test-all: test test-integration ## Run all tests

pull: ## Pull image from ghcr
	docker pull $(IMAGE)

build: ## Build image locally from source
	docker build -t $(IMAGE) .

push: ## Build multi-arch image and push to ghcr
	docker buildx build --platform linux/amd64,linux/arm64 -t $(IMAGE) --push .

install: build ## Build image and install wrapper to /usr/local/bin
	sudo install -m 755 mdpdf-wrapper /usr/local/bin/mdpdf
