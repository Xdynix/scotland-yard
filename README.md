# scotland-yard

A lightweight FastAPI application that simulates an OAuth2-style authorization flow for
multi-tenant organizations.

It provides CRUD-style endpoints for organizations, users, items (files & folders) and
sharing links, all backed by Tortoise ORM with cursor-based pagination.

Designed purely as a demo of FastAPI's dependency injection, Pydantic models, and
automatic OpenAPI documentation.

## Development

Prerequisite:

- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)
- [Docker](https://docs.docker.com/get-started/get-docker/)

Environment setup: `just dev-setup`

Run linters: `just lint`

Run tests: `just test`

Start development server: `just dev`

## Deployment

`docker compose up -d`
