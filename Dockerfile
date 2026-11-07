FROM python:3.14-alpine3.24

ARG APPNAME=car_api

SHELL ["/bin/sh", "-o", "pipefail", "-c"]
ENV PATH="${PATH}:/home/${APPNAME}/.local/bin"\
    POETRY_VERSION=2.5.1 \
    POETRY_VIRTUALENVS_IN_PROJECT=True \
    POETRY_NO_INTERACTION=1

RUN apk add --no-cache curl && \
    adduser -s /bin/sh -D ${APPNAME}

USER ${APPNAME}
WORKDIR /home/${APPNAME}

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock ./

RUN poetry install \
        --no-root \
        --no-ansi \
        --without dev

COPY . .

CMD ["poetry", "run", "fastapi", "run", "car_api/app.py"]