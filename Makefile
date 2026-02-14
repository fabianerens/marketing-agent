.PHONY: help install install-dev run test test-cov clean format lint setup

# Default target
help:
	@echo "YouTube Marketing Agent - Makefile Commands"
	@echo "============================================"
	@echo ""
	@echo "Setup:"
	@echo "  make setup        - Complete first-time setup (install + .env)"
	@echo "  make install      - Install dependencies"
	@echo "  make install-dev  - Install dependencies + dev tools"
	@echo ""
	@echo "Run:"
	@echo "  make run          - Start Gradio app"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run unit tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Lint code with ruff"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove cache, build files"
	@echo "  make clean-cache  - Clear YouTube API cache"

# Complete setup for first time
setup: install
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file from .env.example"; \
		echo ""; \
		echo "⚠️  IMPORTANT: Edit .env and add your API keys:"; \
		echo "   - YOUTUBE_API_KEY"; \
		echo "   - GOOGLE_API_KEY"; \
		echo ""; \
	else \
		echo "✓ .env file already exists"; \
	fi
	@mkdir -p data
	@echo "✓ Created data/ directory for cache"
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "1. Edit .env and add your API keys"
	@echo "2. Run: make run"

# Install dependencies (production)
install:
	@echo "Installing dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv sync; \
	else \
		echo "uv not found, using pip..."; \
		pip install -e .; \
	fi
	@echo "✓ Dependencies installed"

# Install dependencies + dev tools
install-dev:
	@echo "Installing dependencies + dev tools..."
	@if command -v uv >/dev/null 2>&1; then \
		uv sync --all-extras; \
	else \
		echo "uv not found, using pip..."; \
		pip install -e ".[dev]"; \
	fi
	@echo "✓ Dev dependencies installed"

# Run Gradio app
run:
	@echo "Starting YouTube Marketing Agent..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python -m app.gradio_app; \
	else \
		python -m app.gradio_app; \
	fi

# Run tests
test:
	@echo "Running tests..."
	pytest

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=core --cov=agent --cov-report=html --cov-report=term
	@echo ""
	@echo "✓ Coverage report generated in htmlcov/index.html"

# Format code
format:
	@echo "Formatting code..."
	black core/ agent/ app/ tests/
	@echo "✓ Code formatted"

# Lint code
lint:
	@echo "Linting code..."
	ruff check core/ agent/ app/ tests/
	@echo "✓ Linting complete"

# Clean build artifacts
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage build/ dist/ *.egg-info
	@echo "✓ Cleaned build artifacts"

# Clear API cache
clean-cache:
	@echo "Clearing YouTube API cache..."
	rm -rf data/cache.db
	@echo "✓ Cache cleared"
