# Telemetry (OpenTelemetry) 

You can enable tracing with OpenTelemetry. The app performs a **best-effort** initialization at startup and will not crash if OpenTelemetry packages are missing.

## Environment variables

- `OTEL_SERVICE_NAME` — override the service name (default: `medical-pacs`).
- `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_HEADERS` — configure OTLP exporter endpoint and headers.
- `OTEL_TRACES_EXPORTER=otlp` — select the OTLP exporter when applicable.

## Examples

- Local development (console exporter - default):

```bash
export OTEL_SERVICE_NAME="medical-pacs"
python -m src.app.main
# spans will be printed to stdout via the ConsoleSpanExporter
```

- Production using OTLP exporter:

```bash
export OTEL_SERVICE_NAME="medical-pacs"
export OTEL_TRACES_EXPORTER="otlp"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel-collector.example:4317"
export OTEL_EXPORTER_OTLP_HEADERS="api-key=YOUR_KEY"
python -m src.app.main
```

If you prefer not to see console spans in production, call `init_telemetry(enable_console_exporter=False)` in `app/main.py` after setting up environment variables.

