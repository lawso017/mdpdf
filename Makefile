.PHONY: test test-integration test-all build install

test: ## Run unit tests (no Docker needed)
	uv run pytest tests/ -v --ignore=tests/test_integration.py

test-integration: build ## Run integration tests (requires Docker)
	docker run --rm \
		-v $(PWD)/tests:/opt/mdpdf/tests \
		--entrypoint uv \
		mdpdf:latest \
		--directory /opt/mdpdf run pytest tests/test_integration.py -v -m integration

test-all: test test-integration ## Run all tests

build: ## Build Docker image
	docker build -t mdpdf:latest .

install: build ## Build image and install wrapper to /usr/local/bin
	cp mdpdf-wrapper /usr/local/bin/mdpdf
	chmod +x /usr/local/bin/mdpdf
