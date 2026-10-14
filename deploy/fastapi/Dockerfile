FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000 KIKI_REQUIRE_PROXY=1 KIKI_DATA_DIR=/var/data/kiki
WORKDIR /app
COPY prototypes/screen_capture/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt
COPY contracts/__init__.py contracts/screen_capture.py contracts/lab_tracking.py contracts/mixed_language.py /app/contracts/
COPY prototypes/screen_capture/ /app/prototypes/screen_capture/
COPY prototypes/lab_tracking/ /app/prototypes/lab_tracking/
COPY prototypes/backend/ /app/prototypes/backend/
COPY prototypes/mixed_language/ /app/prototypes/mixed_language/
COPY prototypes/mixed_script/pipeline.py prototypes/mixed_script/speech.py /app/prototypes/mixed_script/
COPY docs/architecture/examples/dsb-sc.demo-definition.json /app/docs/architecture/examples/dsb-sc.demo-definition.json
RUN mkdir -p /var/data/kiki
EXPOSE 10000
CMD ["python", "-B", "-m", "prototypes.backend", "--host", "0.0.0.0"]
