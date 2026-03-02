"""
Log Producer - Generates and sends application logs to Kafka
Simulates real-world application logging with various log levels and patterns
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from typing import Any, Dict

from kafka.errors import KafkaError

from kafka import KafkaProducer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LogProducer:
    """Produces application logs to Kafka topic"""

    def __init__(self):
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
        self.topic = os.getenv("LOG_TOPIC", "application-logs")
        self.interval = int(os.getenv("LOG_PRODUCER_INTERVAL_MS", 1000)) / 1000
        self.batch_size = int(os.getenv("LOG_PRODUCER_BATCH_SIZE", 10))

        # Initialize Kafka Producer
        self.producer = self._create_producer()

        # Log level distribution (weighted)
        self.log_levels = [
            "DEBUG",
            "INFO",
            "INFO",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]

        # Sample services and components
        self.services = [
            "api-gateway",
            "auth-service",
            "user-service",
            "payment-service",
            "notification-service",
            "analytics-service",
            "order-service",
            "inventory-service",
            "shipping-service",
            "recommendation-engine",
        ]

        # Sample log messages by level
        self.log_messages = {
            "DEBUG": [
                "Processing request from client",
                "Database query executed successfully",
                "Cache hit for key",
                "Function execution started",
                "Validation passed for input data",
                "Configuration loaded successfully",
            ],
            "INFO": [
                "User logged in successfully",
                "New order created",
                "Payment processed",
                "Email notification sent",
                "API request completed",
                "Data synchronization completed",
                "Cache refreshed",
                "Scheduled job executed",
                "File uploaded successfully",
                "Report generated",
            ],
            "WARNING": [
                "High memory usage detected",
                "Response time exceeding threshold",
                "Rate limit approaching",
                "Deprecated API endpoint used",
                "Cache miss - loading from database",
                "Retry attempt initiated",
                "Connection pool near capacity",
                "Disk space running low",
            ],
            "ERROR": [
                "Database connection failed",
                "Payment gateway timeout",
                "Invalid input data received",
                "External API returned error",
                "File not found",
                "Authentication failed",
                "JSON parsing error",
                "Network timeout occurred",
                "Resource allocation failed",
                "Session expired",
            ],
            "CRITICAL": [
                "Database cluster is down",
                "All payment gateways unreachable",
                "Memory limit exceeded - service crashing",
                "Security breach detected",
                "Data corruption identified",
                "Critical service dependency unavailable",
            ],
        }

        # HTTP status codes
        self.status_codes = {
            "DEBUG": [200],
            "INFO": [200, 201, 202, 204],
            "WARNING": [400, 401, 403, 429],
            "ERROR": [404, 500, 502, 503],
            "CRITICAL": [500, 503],
        }

        # User agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0",
            "PostmanRuntime/7.36.0",
            "Python/3.11 requests/2.31.0",
            "Mobile App/2.5.0 (iOS 17.0)",
            "Mobile App/2.5.0 (Android 14)",
        ]

        # API endpoints
        self.endpoints = [
            "/api/v1/users",
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/orders",
            "/api/v1/products",
            "/api/v1/payments",
            "/api/v1/notifications",
            "/api/v1/analytics",
            "/api/v1/search",
            "/api/v1/recommendations",
            "/api/v1/reviews",
            "/api/v1/cart",
        ]

        logger.info(
            f"Log Producer initialized - Brokers: {self.kafka_brokers}, Topic: {self.topic}"
        )

    def _create_producer(self) -> KafkaProducer:
        """Create and configure Kafka producer"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                compression_type=os.getenv("PRODUCER_COMPRESSION_TYPE", "gzip"),
                batch_size=int(os.getenv("PRODUCER_BATCH_SIZE", 16384)),
                linger_ms=int(os.getenv("PRODUCER_LINGER_MS", 10)),
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=5,
            )
            logger.info("Kafka producer created successfully")
            return producer
        except KafkaError as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            sys.exit(1)

    def generate_log_entry(self) -> Dict[str, Any]:
        """Generate a realistic log entry"""
        log_level = random.choice(self.log_levels)
        service = random.choice(self.services)
        message = random.choice(self.log_messages[log_level])
        status_code = random.choice(self.status_codes[log_level])

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": log_level,
            "service": service,
            "message": message,
            "logger_name": f"{service}.{random.choice(['controller', 'service', 'repository', 'util'])}",
            "thread": f"thread-{random.randint(1, 20)}",
            "request_id": self._generate_request_id(),
            "user_id": f"user_{random.randint(1000, 9999)}"
            if random.random() > 0.3
            else None,
            "session_id": self._generate_session_id(),
            "ip_address": self._generate_ip(),
            "user_agent": random.choice(self.user_agents),
            "endpoint": random.choice(self.endpoints),
            "method": random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"]),
            "status_code": status_code,
            "response_time_ms": self._generate_response_time(log_level),
            "environment": os.getenv("NODE_ENV", "development"),
            "version": "1.0.0",
            "hostname": f"{service}-pod-{random.randint(1, 5)}",
            "region": random.choice(
                ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]
            ),
            "tags": self._generate_tags(log_level, service),
            "metadata": {
                "source": "application",
                "pipeline": "kafka-elk",
                "processed": False,
            },
        }

        # Add error details for ERROR and CRITICAL logs
        if log_level in ["ERROR", "CRITICAL"]:
            log_entry["error"] = {
                "type": random.choice(
                    [
                        "DatabaseError",
                        "NetworkError",
                        "ValidationError",
                        "AuthenticationError",
                        "TimeoutError",
                        "ServiceUnavailable",
                    ]
                ),
                "stack_trace": self._generate_stack_trace(),
                "error_code": f"ERR_{random.randint(1000, 9999)}",
            }

        return log_entry

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

    def _generate_session_id(self) -> str:
        """Generate session ID"""
        return f"sess_{random.randint(100000, 999999)}"

    def _generate_ip(self) -> str:
        """Generate random IP address"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

    def _generate_response_time(self, log_level: str) -> int:
        """Generate realistic response time based on log level"""
        if log_level == "DEBUG":
            return random.randint(10, 50)
        elif log_level == "INFO":
            return random.randint(50, 200)
        elif log_level == "WARNING":
            return random.randint(200, 500)
        elif log_level == "ERROR":
            return random.randint(500, 2000)
        else:  # CRITICAL
            return random.randint(2000, 5000)

    def _generate_tags(self, log_level: str, service: str) -> list:
        """Generate relevant tags"""
        tags = [service, log_level.lower()]

        if log_level in ["ERROR", "CRITICAL"]:
            tags.append("needs-attention")

        if random.random() > 0.7:
            tags.append("production")

        return tags

    def _generate_stack_trace(self) -> str:
        """Generate sample stack trace"""
        files = ["app.py", "service.py", "database.py", "utils.py", "middleware.py"]
        functions = [
            "process_request",
            "handle_error",
            "execute_query",
            "validate_data",
            "authenticate",
        ]

        trace_lines = []
        for i in range(random.randint(3, 6)):
            file = random.choice(files)
            func = random.choice(functions)
            line = random.randint(10, 500)
            trace_lines.append(f'  File "{file}", line {line}, in {func}')

        return "\n".join(trace_lines)

    def send_log(self, log_entry: Dict[str, Any]):
        """Send log entry to Kafka"""
        try:
            # Use service name as key for partitioning
            key = log_entry["service"]

            future = self.producer.send(self.topic, key=key, value=log_entry)

            # Wait for acknowledgment
            record_metadata = future.get(timeout=10)

            logger.debug(
                f"Log sent - Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )

        except KafkaError as e:
            logger.error(f"Failed to send log to Kafka: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while sending log: {e}")

    def produce_logs(self):
        """Main loop to continuously produce logs"""
        logger.info(
            f"Starting log production - Interval: {self.interval}s, Batch size: {self.batch_size}"
        )

        message_count = 0

        try:
            while True:
                # Generate batch of logs
                for _ in range(self.batch_size):
                    log_entry = self.generate_log_entry()
                    self.send_log(log_entry)
                    message_count += 1

                # Flush producer to ensure delivery
                self.producer.flush()

                if message_count % 100 == 0:
                    logger.info(f"Produced {message_count} log messages")

                # Wait before next batch
                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("Shutting down log producer...")
        except Exception as e:
            logger.error(f"Error in log production loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        logger.info(f"Flushing remaining messages...")
        self.producer.flush()
        self.producer.close()
        logger.info("Log producer shut down successfully")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting Application Log Producer")
    logger.info("=" * 60)

    producer = LogProducer()
    producer.produce_logs()


if __name__ == "__main__":
    main()
