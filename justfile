set dotenv-load := true
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

export PYTHONUTF8 := "1"
export LOGURU_COLORIZE := "1"

default: lint test

# set up development environment
dev-setup:
    uv sync
    uv run pre-commit install

# execute linters
lint:
    uv run pre-commit run --all-files

# execute tests
test:
    docker compose -f docker-compose.yaml -f docker-compose.test.yaml up --abort-on-container-exit --exit-code-from app --build

# start development server
dev:
    docker compose -f docker-compose.yaml -f docker-compose.dev.yaml watch

# start interactive Python shell
pyshell:
    docker compose exec -it app tortoise-cli -c app.settings.TORTOISE_ORM shell

# start interactive database shell
dbshell:
    docker compose exec -it postgres bash -c 'psql -U $POSTGRES_USER -h localhost'
