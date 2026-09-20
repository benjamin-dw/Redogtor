FROM python:3.12-slim

RUN useradd --system --no-create-home redactor
WORKDIR /app

RUN pip install --no-cache-dir \
      flask waitress "spacy>=3.8,<3.9" \
      presidio-analyzer presidio-anonymizer \
      python-docx pypdf reportlab \
 && pip install --no-cache-dir \
      https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl

COPY app.py /app/app.py

ENV REDACTOR_MODEL=en_core_web_lg \
    REDACTOR_PORT=8765 \
    REDACTOR_HOST=0.0.0.0 \
    PYTHONDONTWRITEBYTECODE=1

USER redactor
EXPOSE 8765
CMD ["python", "/app/app.py"]
