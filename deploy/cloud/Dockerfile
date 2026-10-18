FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 KIKI_REQUIRE_PROXY=1
WORKDIR /app
COPY deploy/cloud/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt
COPY contracts/ /app/contracts/
COPY prototypes/cloud_lab/ /app/prototypes/cloud_lab/
COPY prototypes/screen_capture/ /app/prototypes/screen_capture/
COPY prototypes/lab_tracking/ /app/prototypes/lab_tracking/
COPY prototypes/backend/lab_idempotency.py /app/prototypes/backend/lab_idempotency.py
COPY prototypes/json_stream/ /app/prototypes/json_stream/
COPY docs/architecture/examples/ /app/docs/architecture/examples/
USER 65532:65532
EXPOSE 8080
CMD ["python", "-B", "-m", "prototypes.cloud_lab"]
