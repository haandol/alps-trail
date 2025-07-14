# ALPS Trail Development Guideline

This file serves as a high-level reference guide for the `alps-trail` repository.
It summarizes the purpose of the project, directory layout, and how to build or run the available tools.

## Overview

ALPS Trail (Task Refinement and Iterative Linking) is a tool that parses ALPS specifications and automatically breaks down features into smaller tasks.
The goal is to simplify planning by producing a YAML task list that captures task dependencies in a Directed Acyclic Graph (DAG).

## Dependencies

- Go 1.24+
- [Cobra CLI framework](https://github.com/spf13/cobra)
- Docker

## Directory Structure

- `src/` – Python modules including the main ALPS parser (`parser.py`).
- `cmd/` – A minimal Go command line interface (`alps-trail`), demonstrating a basic workflow.
- `specs/` – Example and template ALPS specification documents.
- `README.md` – Project description, installation instructions, and usage examples.

## ALPS Specification Document Structure

- ALPS specific documentation template is in `specs/template.md`.
- ALPS spec document has 8 sections.
  - Section 1: Overview
  - Section 2: MVP Goals and Key Metrics
  - Section 3: Requirements Summary
  - Section 4: High-Level Architecture
  - Section 5: Design Specification
  - Section 6: Feature-Level Specification
  - Section 7: MVP Metrics
  - Section 8: Out-of-Scope

## Usage

### Parse ALPS spec document

parse ALPS spec document and extract sections into a structured format (markdown).

```bash
alps-trail parse <path_to_alps_doc.md> -o ./sections.md -v
```

### Generate task list

generate task list from the parsed sections.

```bash
alps-trail generate <path_to_sections.md> -o ./tasks.yaml -v
```

### Breakdown task

breakdown task list into smaller tasks.
- if task id is not provided, error will be raised.
- task id is a unique identifier for the task.
- if output file is provided, it will be overwritten.

```bash
alps-trail breakdown <path_to_tasks.yaml> --id <task_id> -o ./tasks.yaml -v
```

## Further Reading

For best practices on configuring `AGENTS.md` files, see [the VibeCoding article](https://www.vibecoding.com/2025/06/05/how-to-configure-agents-md-files-to-supercharge-your-codex-ai-agent-performance/).
