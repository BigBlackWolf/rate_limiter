ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_HOME="/opt/poetry"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

WORKDIR /app

FROM base as builder-base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        # deps for installing poetry
        curl \
        # deps for building python deps
        build-essential


RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml ./

RUN poetry install

COPY ./src/ .

ENV RATE_LIMITER_LIMIT=0 \
    RATE_LIMITER_NUMBER_OF_TOKENS=10 \
    RATE_LIMITER_WINDOW=60

EXPOSE 8000

CMD poetry run uvicorn rate_limiter.main:app --host 0.0.0.0 --port 8000