# Python's own image by digest, and every package from requirements.txt by hash.
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

RUN useradd --system --no-create-home redactor
WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check --require-hashes --no-deps --only-binary :all: \
      -r /tmp/requirements.txt \
 && pip check \
 && rm /tmp/requirements.txt

COPY app.py /app/app.py

ENV REDACTOR_MODEL=en_core_web_lg \
    REDACTOR_PORT=8765 \
    REDACTOR_HOST=0.0.0.0 \
    PYTHONDONTWRITEBYTECODE=1

USER redactor
EXPOSE 8765
CMD ["python", "/app/app.py"]
