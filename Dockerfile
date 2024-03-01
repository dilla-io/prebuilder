FROM python:3-alpine

LABEL name="dilla-prebuilder"
LABEL maintainer="pierre@dilla.io"
LABEL version="1.0.0"
LABEL description="Dilla prebuilder for project https://dilla.io"
LABEL org.label-schema.schema-version="1.0.0"
LABEL org.label-schema.name="dillaio/prebuilder"
LABEL org.label-schema.description="Dilla prebuilder for project https://dilla.io"
LABEL org.label-schema.url="https://gitlab.com/dilla-io/prebuilder"
LABEL org.label-schema.vcs-url="https://gitlab.com/dilla-io/prebuilder.git"
LABEL org.label-schema.vendor="dilla.io"

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY templates/rust.jinja ./templates/rust.jinja

ENTRYPOINT [ "python", "prebuilder.py" ]

