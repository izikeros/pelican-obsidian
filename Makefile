# Sets the default shell for executing commands as /bin/bash and specifies command should be executed in a Bash shell.
SHELL := /bin/bash

# Color codes for terminal output
COLOR_RESET=\033[0m
COLOR_CYAN=\033[1;36m
COLOR_GREEN=\033[1;32m

SRC_FILES = pelican
SRC_AND_TEST_FILES = pelican

# Use conditional logic to adapt commands for macOS vs. Linux.
SED_CMD := $(shell if [ "$(shell uname)" = "Darwin" ]; then echo "gsed"; else echo "sed"; fi)


# Defines the targets help, install, dev-install, and run as phony targets.
#  Phony targets are targets that are not really the name of files that are to be built.
#  Instead, they are treated as commands.
.PHONY: help install create-env create-venv install-deps farewell clean test coverage coverage-show format lint lint-stats fix type audit license license-unapproved-licenses license-unapproved-packages requirements-txt bandit

# Sets the default goal to help when no target is specified on the command line.
.DEFAULT_GOAL := help

# Disables echoing of commands. The commands executed by Makefile will not be
#  printed on the console during execution.
.SILENT:

help: ## Show all Makefile targets.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'

format: ## Running code formatter: black and isort
	@echo "(black) Formatting codebase..."
	black --config pyproject.toml $(SRC_AND_TEST_FILES)
	@echo "(ruff) Running fix only..."
	ruff check $(SRC_AND_TEST_FILES) --fix-only

lint: ## Run the linter (ruff) to check the code style.
	@echo -e "$(COLOR_CYAN)Checking code style with ruff...$(COLOR_RESET)"
	ruff check $(SRC_AND_TEST_FILES)

fix: ## Run ruff and fix the issues that are fixable automatically.
	@echo -e "$(COLOR_CYAN)Fixing code style issues with ruff...$(COLOR_RESET)"
	ruff check $(SRC_AND_TEST_FILES) databricks --fix

changelog: ## Generate a changelog using git-cliff
	git-cliff -o CHANGELOG.md
