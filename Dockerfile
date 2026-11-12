# Python's own image by digest, and every package from requirements.txt by hash.
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

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
