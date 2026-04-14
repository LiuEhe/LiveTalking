---
name: Code Standards and Guidelines
description: Strict coding guidelines for the LiveTalking backend project, covering configuration management, architecture layering, and code review processes.
---

# LiveTalking Project Code Standards

When writing, refactoring, or reviewing code for the LiveTalking backend, you MUST strictly adhere to the following rules:

## 1. No Hardcoding (禁止硬编码)
- **Configuration & Models**: You are strictly prohibited from hardcoding any configuration values, model paths, API URLs, or environment-specific variables directly in the code.
- **Config Management**: ALL configuration data must be read from the central `config.json` file. Whenever you need a new constant or setting, add it to `config.json` rather than hardcoding it.

## 2. Three-Layer Architecture (3层代码规范)
The backend codebase must strictly follow a three-layer architecture to ensure decoupling and maintainability. Every layer directory MUST use an `__init__.py` file to explicitly export its public interfaces (e.g., routers, core functions, server state).
- **API Layer (`api/`)**: Responsible for defining routes, handling HTTP/WebSocket requests, and performing parameter validation. API routes MUST include a versioning prefix (e.g., `/api/v1`), such as `/api/v1/chat`. All individual API routers must be bundled and exported by `api/__init__.py`. No business logic should reside here.
- **Server Layer (`servers/`)**: Responsible for processing business logic, managing state, and executing operations (such as communicating with LLMs or media streams).
- **Core Layer (`core/`)**: Responsible for base system functionality, including loading configurations (from `config.json`), setting up databases, handling dependencies, and security.

## 3. Mandatory Code Review (严格代码 Review)
- **Quality Assurance**: After completing any code modifications or feature additions, you must perform a self-review of the changes.
- **Correctness**: Ensure that the code functions flawlessly without typos, properly handles errors, and correctly implements the required features. The code must meet a correctness rate of strictly > 0.9 before it is considered done.

## 4. Standardized Imports (规范导入)
- **Imports at Top**: ALL `import` and `from ... import ...` statements MUST be placed at the top of the file. Do not import libraries in the middle of code or inside functions.
- **Package-Level Imports**: Cross-layer code MUST import endpoints via the target layer's `__init__.py` instead of digging into specific sub-files. (e.g., use `from core import load_model` instead of `from core.lipreal import load_model`).
