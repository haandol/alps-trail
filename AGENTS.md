# Project Wiki: ALPS Trail

This file serves as a high-level reference guide for the `alps-trail` repository. It summarizes the purpose of the project, directory layout, and how to build or run the available tools.

## Overview

ALPS Trail (Task Refinement and Iterative Linking) is a tool that parses ALPS specifications and automatically breaks down features into smaller tasks. The goal is to simplify planning by producing a YAML task list that captures task dependencies in a Directed Acyclic Graph (DAG).

## Directory structure

- `src/` – Python modules including the main ALPS parser (`parser.py`).
- `cmd/` – A minimal Go command line interface (`alps`), demonstrating a basic workflow.
- `specs/` – Example ALPS specification documents.
- `README.md` – Project description, installation instructions, and usage examples.

## Usage

### Python

Install the package in editable mode:

```bash
git clone <repo>
cd alps-trail
uv pip install -e .
```

Run the main command to process an ALPS file:

```bash
alps-trail breakdown <path_to_alps_doc.md> -o ./tasks.yaml -v
```

### Go

Build and run the simplified CLI:

```bash
go build ./cmd/alps
./alps-breakdown process <spec_file.md> --output tasks.yaml --verbose
```

## Further Reading

For best practices on configuring `AGENTS.md` files, see [the VibeCoding article](https://www.vibecoding.com/2025/06/05/how-to-configure-agents-md-files-to-supercharge-your-codex-ai-agent-performance/).
