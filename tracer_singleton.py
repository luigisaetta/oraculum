"""
Tracer Singleton

    to support integration with OCI APM
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.resources import Resource
from config_reader import ConfigReader
from config_private import APM_PUBLIC_KEY
from utils import get_console_logger


class NoopSpanExporter(SpanExporter):
    """
    NoOp exporter for OpenTelemetry
    """

    def export(self, spans):
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


logger = get_console_logger()


class TracerSingleton:
    """
    Singleton to handle tracing with OPenTelemetry to OCI APM
    """

    _instance = None

    @staticmethod
    def get_instance():
        """
        return the single instance
        """
        if TracerSingleton._instance is None:
            # Inizializza il tracer al primo accesso
            TracerSingleton._instance = TracerSingleton._init_tracer()
        return TracerSingleton._instance

    @staticmethod
    def _init_tracer():
        """
        Init tracer for APM integration, leggendo i parametri dalla configurazione.
        """
        # Legge la configurazione dal file (puoi personalizzare il percorso)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "config.toml")
        config = ConfigReader(config_path)

        trace_enable = config.find_key("trace_enable")
        apm_endpoint = config.find_key("apm_endpoint")
        service_name = config.find_key("service_name")
        tracer_name = config.find_key("tracer_name")

        # Configura il tracer
        resource = Resource(attributes={"service.name": service_name})
        provider = TracerProvider(resource=resource)

        if trace_enable:
            # Configura l'exporter OTLP se tracing è abilitato
            logger.info("Enabling APM tracing...")

            exporter = OTLPSpanExporter(
                endpoint=apm_endpoint,
                headers={"authorization": f"dataKey {APM_PUBLIC_KEY}"},
            )
        else:
            # Usa un NoOpSpanExporter per scartare le trace
            exporter = NoopSpanExporter()

        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)

        # Restituisce il tracer configurato
        return trace.get_tracer(tracer_name)
