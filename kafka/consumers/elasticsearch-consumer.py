"""
Elasticsearch Consumer - Consumes messages from Kafka and indexes them in Elasticsearch
Handles logs, metrics, and events with proper error handling and retry logic
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ElasticsearchException
from kafka.errors import KafkaError

from kafka import KafkaConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ElasticsearchConsumer:
    """Consumes messages from Kafka and indexes them in Elasticsearch"""

    def __init__(self):
        # Kafka configuration
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
        self.consumer_group = os.getenv("CONSUMER_GROUP", "elasticsearch-consumers")
        self.topics = self._get_topics()

        # Elasticsearch configuration
        self.es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.index_prefix = os.getenv("ELASTICSEARCH_INDEX_PREFIX", "pipeline")

        # Performance tuning
        self.batch_size = int(os.getenv("ES_BATCH_SIZE", 500))
        self.flush_interval = int(os.getenv("ES_FLUSH_INTERVAL", 5))

        # Initialize connections
        self.consumer = self._create_consumer()
        self.es_client = self._create_es_client()

        # Message buffer for batch indexing
        self.message_buffer = []
        self.last_flush_time = time.time()

        # Statistics
        self.stats = {"consumed": 0, "indexed": 0, "failed": 0, "batches": 0}

        logger.info(f"Elasticsearch Consumer initialized")
        logger.info(f"Kafka Brokers: {self.kafka_brokers}")
        logger.info(f"Topics: {self.topics}")
        logger.info(f"Elasticsearch: {self.es_url}")

    def _get_topics(self) -> List[str]:
        """Get list of topics to consume"""
        topics = []

        log_topic = os.getenv("LOG_TOPIC", "application-logs")
        metrics_topic = os.getenv("METRICS_TOPIC", "system-metrics")
        events_topic = os.getenv("EVENTS_TOPIC", "business-events")

        topics.extend([log_topic, metrics_topic, events_topic])

        return topics

    def _create_consumer(self) -> KafkaConsumer:
        """Create and configure Kafka consumer"""
        try:
            consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.kafka_brokers,
                group_id=self.consumer_group,
                auto_offset_reset=os.getenv("CONSUMER_AUTO_OFFSET_RESET", "earliest"),
                enable_auto_commit=False,  # Manual commit for better control
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                max_poll_records=int(os.getenv("CONSUMER_MAX_POLL_RECORDS", 500)),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_interval_ms=300000,
            )
            logger.info("Kafka consumer created successfully")
            return consumer
        except KafkaError as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            sys.exit(1)

    def _create_es_client(self) -> Elasticsearch:
        """Create and configure Elasticsearch client"""
        try:
            # Parse Elasticsearch URL
            es_config = {
                "hosts": [self.es_url],
                "retry_on_timeout": True,
                "max_retries": 3,
                "request_timeout": 30,
            }

            # Add authentication if provided
            es_username = os.getenv("ELASTICSEARCH_USERNAME")
            es_password = os.getenv("ELASTICSEARCH_PASSWORD")

            if es_username and es_password:
                es_config["basic_auth"] = (es_username, es_password)

            client = Elasticsearch(**es_config)

            # Test connection
            if client.ping():
                logger.info("Connected to Elasticsearch successfully")
                info = client.info()
                logger.info(f"Elasticsearch version: {info['version']['number']}")
            else:
                logger.error("Failed to connect to Elasticsearch")
                sys.exit(1)

            # Create index templates
            self._create_index_templates(client)

            return client

        except ElasticsearchException as e:
            logger.error(f"Failed to create Elasticsearch client: {e}")
            sys.exit(1)

    def _create_index_templates(self, client: Elasticsearch):
        """Create index templates for different data types"""

        # Template for logs
        logs_template = {
            "index_patterns": [f"{self.index_prefix}-logs-*"],
            "template": {
                "settings": {
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                    "refresh_interval": "5s",
                    "index.codec": "best_compression",
                },
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "level": {"type": "keyword"},
                        "service": {"type": "keyword"},
                        "message": {"type": "text"},
                        "logger_name": {"type": "keyword"},
                        "request_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "ip_address": {"type": "ip"},
                        "endpoint": {"type": "keyword"},
                        "method": {"type": "keyword"},
                        "status_code": {"type": "integer"},
                        "response_time_ms": {"type": "integer"},
                        "environment": {"type": "keyword"},
                        "region": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                    }
                },
            },
        }

        # Template for metrics
        metrics_template = {
            "index_patterns": [f"{self.index_prefix}-metrics-*"],
            "template": {
                "settings": {
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                    "refresh_interval": "10s",
                    "index.codec": "best_compression",
                },
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "service": {"type": "keyword"},
                        "hostname": {"type": "keyword"},
                        "region": {"type": "keyword"},
                        "environment": {"type": "keyword"},
                        "instance_id": {"type": "keyword"},
                        "instance_type": {"type": "keyword"},
                        "health_status": {"type": "keyword"},
                        "cpu": {"type": "object", "enabled": True},
                        "memory": {"type": "object", "enabled": True},
                        "disk": {"type": "object", "enabled": True},
                        "network": {"type": "object", "enabled": True},
                        "application": {"type": "object", "enabled": True},
                    }
                },
            },
        }

        # Template for events
        events_template = {
            "index_patterns": [f"{self.index_prefix}-events-*"],
            "template": {
                "settings": {
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                    "refresh_interval": "5s",
                },
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "event_type": {"type": "keyword"},
                        "service": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "event_data": {"type": "object", "enabled": True},
                    }
                },
            },
        }

        # Create templates
        try:
            # For Elasticsearch 8.x, use put_index_template
            client.indices.put_index_template(
                name=f"{self.index_prefix}-logs-template", body=logs_template
            )
            logger.info("Created logs index template")

            client.indices.put_index_template(
                name=f"{self.index_prefix}-metrics-template", body=metrics_template
            )
            logger.info("Created metrics index template")

            client.indices.put_index_template(
                name=f"{self.index_prefix}-events-template", body=events_template
            )
            logger.info("Created events index template")

        except Exception as e:
            logger.warning(f"Failed to create index templates: {e}")

    def _get_index_name(self, topic: str) -> str:
        """Generate index name based on topic and date"""
        date_str = datetime.utcnow().strftime("%Y.%m.%d")

        if "log" in topic.lower():
            return f"{self.index_prefix}-logs-{date_str}"
        elif "metric" in topic.lower():
            return f"{self.index_prefix}-metrics-{date_str}"
        elif "event" in topic.lower():
            return f"{self.index_prefix}-events-{date_str}"
        else:
            return f"{self.index_prefix}-data-{date_str}"

    def _prepare_document(self, message: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """Prepare document for indexing"""
        doc = message.copy()

        # Add metadata
        doc["_kafka_topic"] = topic
        doc["_indexed_at"] = datetime.utcnow().isoformat() + "Z"

        # Ensure timestamp field exists
        if "timestamp" not in doc:
            doc["timestamp"] = datetime.utcnow().isoformat() + "Z"

        return doc

    def _bulk_index(self, documents: List[Dict[str, Any]]):
        """Bulk index documents to Elasticsearch"""
        if not documents:
            return

        try:
            # Prepare bulk actions
            actions = []
            for doc_info in documents:
                action = {"_index": doc_info["index"], "_source": doc_info["document"]}
                actions.append(action)

            # Execute bulk indexing
            success, failed = helpers.bulk(
                self.es_client,
                actions,
                chunk_size=self.batch_size,
                raise_on_error=False,
                stats_only=False,
            )

            self.stats["indexed"] += success
            self.stats["failed"] += len(failed) if isinstance(failed, list) else failed
            self.stats["batches"] += 1

            logger.info(
                f"Bulk indexed {success} documents, {len(failed) if isinstance(failed, list) else failed} failed"
            )

            if failed:
                logger.error(f"Failed documents: {failed[:5]}")  # Log first 5 failures

        except ElasticsearchException as e:
            logger.error(f"Elasticsearch bulk indexing error: {e}")
            self.stats["failed"] += len(documents)
        except Exception as e:
            logger.error(f"Unexpected error during bulk indexing: {e}")
            self.stats["failed"] += len(documents)

    def _should_flush(self) -> bool:
        """Check if buffer should be flushed"""
        buffer_full = len(self.message_buffer) >= self.batch_size
        time_elapsed = (time.time() - self.last_flush_time) >= self.flush_interval

        return buffer_full or time_elapsed

    def process_message(self, message):
        """Process a single Kafka message"""
        try:
            topic = message.topic
            value = message.value

            # Get index name
            index_name = self._get_index_name(topic)

            # Prepare document
            document = self._prepare_document(value, topic)

            # Add to buffer
            self.message_buffer.append({"index": index_name, "document": document})

            self.stats["consumed"] += 1

            # Check if we should flush
            if self._should_flush():
                self._bulk_index(self.message_buffer)
                self.message_buffer = []
                self.last_flush_time = time.time()

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.stats["failed"] += 1

    def consume(self):
        """Main consumption loop"""
        logger.info("Starting message consumption...")
        logger.info(
            f"Batch size: {self.batch_size}, Flush interval: {self.flush_interval}s"
        )

        try:
            for message in self.consumer:
                self.process_message(message)

                # Commit offsets periodically
                if self.stats["consumed"] % 100 == 0:
                    self.consumer.commit()
                    logger.info(
                        f"Stats - Consumed: {self.stats['consumed']}, "
                        f"Indexed: {self.stats['indexed']}, "
                        f"Failed: {self.stats['failed']}, "
                        f"Batches: {self.stats['batches']}"
                    )

        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
        except Exception as e:
            logger.error(f"Error in consumption loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")

        # Flush remaining messages
        if self.message_buffer:
            logger.info(f"Flushing {len(self.message_buffer)} remaining messages")
            self._bulk_index(self.message_buffer)

        # Commit final offsets
        try:
            self.consumer.commit()
            logger.info("Final offset commit successful")
        except Exception as e:
            logger.error(f"Error committing final offsets: {e}")

        # Close connections
        self.consumer.close()
        self.es_client.close()

        # Print final stats
        logger.info("=" * 60)
        logger.info("FINAL STATISTICS")
        logger.info(f"Total Consumed: {self.stats['consumed']}")
        logger.info(f"Total Indexed: {self.stats['indexed']}")
        logger.info(f"Total Failed: {self.stats['failed']}")
        logger.info(f"Total Batches: {self.stats['batches']}")
        logger.info("=" * 60)


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting Elasticsearch Consumer")
    logger.info("=" * 60)

    consumer = ElasticsearchConsumer()
    consumer.consume()


if __name__ == "__main__":
    main()
