"""
Metrics Producer - Generates and sends system metrics to Kafka
Simulates real-world system monitoring with CPU, memory, disk, and network metrics
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


class MetricsProducer:
    """Produces system metrics to Kafka topic"""

    def __init__(self):
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
        self.topic = os.getenv("METRICS_TOPIC", "system-metrics")
        self.interval = int(os.getenv("METRICS_PRODUCER_INTERVAL_MS", 5000)) / 1000

        # Initialize Kafka Producer
        self.producer = self._create_producer()

        # Services to monitor
        self.services = [
            "api-gateway",
            "auth-service",
            "user-service",
            "payment-service",
            "notification-service",
            "analytics-service",
            "order-service",
            "inventory-service",
            "database-primary",
            "database-replica",
            "cache-redis",
            "message-queue",
        ]

        # Regions
        self.regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]

        # Initialize baseline metrics for realistic patterns
        self.service_baselines = {
            service: {
                "cpu_baseline": random.uniform(20, 40),
                "memory_baseline": random.uniform(30, 50),
                "disk_baseline": random.uniform(40, 60),
                "network_baseline": random.uniform(10, 30),
            }
            for service in self.services
        }

        logger.info(
            f"Metrics Producer initialized - Brokers: {self.kafka_brokers}, Topic: {self.topic}"
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
            )
            logger.info("Kafka producer created successfully")
            return producer
        except KafkaError as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            sys.exit(1)

    def generate_cpu_metrics(self, service: str) -> Dict[str, Any]:
        """Generate CPU metrics"""
        baseline = self.service_baselines[service]["cpu_baseline"]
        variation = random.uniform(-10, 15)
        usage = max(0, min(100, baseline + variation))

        # Simulate occasional spikes
        if random.random() > 0.95:
            usage = min(100, usage + random.uniform(20, 40))

        return {
            "usage_percent": round(usage, 2),
            "user_percent": round(usage * random.uniform(0.6, 0.8), 2),
            "system_percent": round(usage * random.uniform(0.1, 0.3), 2),
            "idle_percent": round(100 - usage, 2),
            "load_average_1m": round(usage / 25, 2),
            "load_average_5m": round(usage / 30, 2),
            "load_average_15m": round(usage / 35, 2),
            "cores": random.choice([2, 4, 8, 16]),
            "context_switches": random.randint(10000, 50000),
            "interrupts": random.randint(5000, 25000),
        }

    def generate_memory_metrics(self, service: str) -> Dict[str, Any]:
        """Generate memory metrics"""
        baseline = self.service_baselines[service]["memory_baseline"]
        variation = random.uniform(-5, 10)
        usage_percent = max(0, min(100, baseline + variation))

        total_mb = random.choice([2048, 4096, 8192, 16384])
        used_mb = int(total_mb * (usage_percent / 100))
        available_mb = total_mb - used_mb

        return {
            "usage_percent": round(usage_percent, 2),
            "total_mb": total_mb,
            "used_mb": used_mb,
            "available_mb": available_mb,
            "free_mb": int(available_mb * random.uniform(0.6, 0.9)),
            "buffers_mb": random.randint(50, 200),
            "cached_mb": random.randint(100, 500),
            "swap_total_mb": int(total_mb * 0.5),
            "swap_used_mb": int(total_mb * 0.5 * random.uniform(0, 0.3)),
            "page_faults": random.randint(100, 1000),
        }

    def generate_disk_metrics(self, service: str) -> Dict[str, Any]:
        """Generate disk metrics"""
        baseline = self.service_baselines[service]["disk_baseline"]
        variation = random.uniform(-2, 5)
        usage_percent = max(0, min(100, baseline + variation))

        total_gb = random.choice([50, 100, 250, 500, 1000])
        used_gb = int(total_gb * (usage_percent / 100))
        available_gb = total_gb - used_gb

        return {
            "usage_percent": round(usage_percent, 2),
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": available_gb,
            "read_mb_per_sec": round(random.uniform(0, 100), 2),
            "write_mb_per_sec": round(random.uniform(0, 50), 2),
            "read_ops_per_sec": random.randint(0, 1000),
            "write_ops_per_sec": random.randint(0, 500),
            "io_util_percent": round(random.uniform(0, 80), 2),
            "read_latency_ms": round(random.uniform(1, 20), 2),
            "write_latency_ms": round(random.uniform(2, 30), 2),
            "inode_usage_percent": round(random.uniform(10, 50), 2),
        }

    def generate_network_metrics(self, service: str) -> Dict[str, Any]:
        """Generate network metrics"""
        baseline = self.service_baselines[service]["network_baseline"]
        variation = random.uniform(-5, 15)
        usage_mbps = max(0, baseline + variation)

        # Simulate traffic spikes
        if random.random() > 0.9:
            usage_mbps += random.uniform(50, 200)

        return {
            "rx_mbps": round(usage_mbps * random.uniform(0.6, 0.8), 2),
            "tx_mbps": round(usage_mbps * random.uniform(0.2, 0.4), 2),
            "rx_packets_per_sec": random.randint(1000, 10000),
            "tx_packets_per_sec": random.randint(500, 5000),
            "rx_errors": random.randint(0, 10),
            "tx_errors": random.randint(0, 5),
            "rx_dropped": random.randint(0, 5),
            "tx_dropped": random.randint(0, 3),
            "connections_active": random.randint(10, 1000),
            "connections_established": random.randint(5, 500),
            "tcp_retransmissions": random.randint(0, 50),
        }

    def generate_application_metrics(self, service: str) -> Dict[str, Any]:
        """Generate application-specific metrics"""
        return {
            "requests_per_sec": random.randint(10, 500),
            "response_time_ms": {
                "p50": round(random.uniform(20, 100), 2),
                "p95": round(random.uniform(100, 500), 2),
                "p99": round(random.uniform(500, 2000), 2),
                "max": round(random.uniform(1000, 5000), 2),
            },
            "error_rate_percent": round(random.uniform(0, 5), 2),
            "success_rate_percent": round(random.uniform(95, 100), 2),
            "active_connections": random.randint(10, 500),
            "queue_size": random.randint(0, 100),
            "thread_pool_active": random.randint(5, 50),
            "thread_pool_size": random.choice([50, 100, 200]),
            "cache_hit_rate_percent": round(random.uniform(70, 95), 2),
            "database_connections_active": random.randint(5, 50),
        }

    def generate_jvm_metrics(self, service: str) -> Dict[str, Any]:
        """Generate JVM metrics (for Java services)"""
        heap_total_mb = random.choice([512, 1024, 2048, 4096])
        heap_used_mb = int(heap_total_mb * random.uniform(0.4, 0.8))

        return {
            "heap_used_mb": heap_used_mb,
            "heap_max_mb": heap_total_mb,
            "heap_usage_percent": round((heap_used_mb / heap_total_mb) * 100, 2),
            "non_heap_used_mb": random.randint(50, 200),
            "gc_young_count": random.randint(0, 100),
            "gc_young_time_ms": random.randint(0, 500),
            "gc_old_count": random.randint(0, 10),
            "gc_old_time_ms": random.randint(0, 2000),
            "threads_live": random.randint(20, 200),
            "threads_daemon": random.randint(10, 100),
            "classes_loaded": random.randint(5000, 20000),
        }

    def generate_metrics_entry(self) -> Dict[str, Any]:
        """Generate complete metrics entry"""
        service = random.choice(self.services)
        region = random.choice(self.regions)

        metrics_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": service,
            "hostname": f"{service}-pod-{random.randint(1, 10)}",
            "region": region,
            "availability_zone": f"{region}{random.choice(['a', 'b', 'c'])}",
            "environment": os.getenv("NODE_ENV", "development"),
            "version": "1.0.0",
            "instance_id": f"i-{random.randint(100000, 999999):06x}",
            "instance_type": random.choice(["t3.small", "t3.medium", "t3.large"]),
            "cpu": self.generate_cpu_metrics(service),
            "memory": self.generate_memory_metrics(service),
            "disk": self.generate_disk_metrics(service),
            "network": self.generate_network_metrics(service),
            "application": self.generate_application_metrics(service),
            "health_status": self._determine_health_status(service),
            "uptime_seconds": random.randint(3600, 2592000),
            "metadata": {
                "source": "metrics-collector",
                "collector_version": "2.0.0",
                "collection_interval_ms": int(self.interval * 1000),
                "pipeline": "kafka-elk",
            },
        }

        # Add JVM metrics for Java services
        if "service" in service and random.random() > 0.5:
            metrics_entry["jvm"] = self.generate_jvm_metrics(service)

        return metrics_entry

    def _determine_health_status(self, service: str) -> str:
        """Determine health status based on metrics"""
        cpu = self.service_baselines[service]["cpu_baseline"]
        memory = self.service_baselines[service]["memory_baseline"]

        if cpu > 80 or memory > 85:
            return "critical"
        elif cpu > 60 or memory > 70:
            return "warning"
        else:
            return "healthy"

    def send_metrics(self, metrics_entry: Dict[str, Any]):
        """Send metrics entry to Kafka"""
        try:
            # Use service name as key for partitioning
            key = metrics_entry["service"]

            future = self.producer.send(self.topic, key=key, value=metrics_entry)

            # Wait for acknowledgment
            record_metadata = future.get(timeout=10)

            logger.debug(
                f"Metrics sent - Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )

        except KafkaError as e:
            logger.error(f"Failed to send metrics to Kafka: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while sending metrics: {e}")

    def produce_metrics(self):
        """Main loop to continuously produce metrics"""
        logger.info(f"Starting metrics production - Interval: {self.interval}s")

        message_count = 0

        try:
            while True:
                # Generate metrics for all services
                for _ in range(len(self.services)):
                    metrics_entry = self.generate_metrics_entry()
                    self.send_metrics(metrics_entry)
                    message_count += 1

                # Flush producer to ensure delivery
                self.producer.flush()

                if message_count % 50 == 0:
                    logger.info(f"Produced {message_count} metric messages")

                # Wait before next collection
                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("Shutting down metrics producer...")
        except Exception as e:
            logger.error(f"Error in metrics production loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Flushing remaining messages...")
        self.producer.flush()
        self.producer.close()
        logger.info("Metrics producer shut down successfully")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting System Metrics Producer")
    logger.info("=" * 60)

    producer = MetricsProducer()
    producer.produce_metrics()


if __name__ == "__main__":
    main()
