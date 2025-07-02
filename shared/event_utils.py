import json
import uuid
from datetime import datetime
from typing import Dict, Any, Callable, Awaitable

import aio_pika
from loguru import logger


class BaseEventPublisher:
    """
    Base class for event publishers to be extended by each service
    """
    def __init__(self, rabbitmq_url: str, service_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.connected = False
    
    async def connect(self) -> None:
        """
        Connect to RabbitMQ broker
        """
        if self.connected:
            return
        
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchanges
            await self.channel.declare_exchange(
                "billing_events", 
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            self.connected = True
            logger.info(f"{self.service_name}: Connected to RabbitMQ broker as publisher")
        except Exception as e:
            logger.error(f"{self.service_name}: Failed to connect to RabbitMQ broker as publisher: {e}")
            self.connected = False
    
    async def disconnect(self) -> None:
        """
        Disconnect from RabbitMQ broker
        """
        if self.connection and self.connected:
            await self.connection.close()
            self.connected = False
            logger.info(f"{self.service_name}: Disconnected from RabbitMQ broker")
    
    async def publish_event(self, routing_key: str, event_data: Dict[str, Any], correlation_id: str = None) -> bool:
        """
        Publish an event to RabbitMQ
        """
        if not self.connected:
            await self.connect()
            if not self.connected:
                return False
        
        try:
            # Create a standardized event format
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_data.get("event_type", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "source_service": self.service_name,
                "payload": event_data.get("payload", {})
            }
            
            exchange = await self.channel.get_exchange("billing_events")
            
            message = aio_pika.Message(
                body=json.dumps(event).encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                correlation_id=correlation_id,
                message_id=event["event_id"]
            )
            
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f"{self.service_name}: Event published: {event['event_type']} with ID {event['event_id']}")
            return True
        except Exception as e:
            logger.error(f"{self.service_name}: Failed to publish event: {e}")
            return False


class BaseEventConsumer:
    """
    Base class for event consumers to be extended by each service
    """
    def __init__(self, rabbitmq_url: str, service_name: str, queue_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.connected = False
        self.event_handlers = {}
    
    async def connect(self) -> None:
        """
        Connect to RabbitMQ broker
        """
        if self.connected:
            return
        
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                "billing_events", 
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            queue = await self.channel.declare_queue(
                self.queue_name, 
                durable=True,
                auto_delete=False
            )
            
            self.connected = True
            logger.info(f"{self.service_name}: Connected to RabbitMQ broker as consumer")
        except Exception as e:
            logger.error(f"{self.service_name}: Failed to connect to RabbitMQ broker as consumer: {e}")
            self.connected = False
    
    async def disconnect(self) -> None:
        """
        Disconnect from RabbitMQ broker
        """
        if self.connection and self.connected:
            await self.connection.close()
            self.connected = False
            logger.info(f"{self.service_name}: Disconnected from RabbitMQ broker as consumer")
    
    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Register a handler for a specific event type
        """
        self.event_handlers[event_type] = handler
        logger.info(f"{self.service_name}: Registered handler for event type: {event_type}")
    
    async def bind_routing_key(self, routing_key: str) -> None:
        """
        Bind the queue to a routing key
        """
        if not self.connected:
            await self.connect()
            if not self.connected:
                logger.error(f"{self.service_name}: Cannot bind routing key, not connected to RabbitMQ")
                return
        
        try:
            exchange = await self.channel.get_exchange("billing_events")
            queue = await self.channel.get_queue(self.queue_name)
            await queue.bind(exchange, routing_key=routing_key)
            logger.info(f"{self.service_name}: Bound queue {self.queue_name} to routing key {routing_key}")
        except Exception as e:
            logger.error(f"{self.service_name}: Failed to bind routing key: {e}")
    
    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        """
        Process an incoming message
        """
        async with message.process():
            try:
                # Parse message body
                body = json.loads(message.body.decode())
                event_type = body.get("event_type")
                
                if event_type and event_type in self.event_handlers:
                    logger.info(f"{self.service_name}: Processing {event_type} event with ID {body.get('event_id')}")
                    await self.event_handlers[event_type](body)
                else:
                    logger.warning(f"{self.service_name}: No handler for event type: {event_type}")
            except json.JSONDecodeError:
                logger.error(f"{self.service_name}: Failed to decode message body as JSON")
            except Exception as e:
                logger.error(f"{self.service_name}: Error processing message: {e}")
    
    async def start_consuming(self) -> None:
        """
        Start consuming messages
        """
        if not self.connected:
            await self.connect()
            if not self.connected:
                logger.error(f"{self.service_name}: Cannot start consuming, not connected to RabbitMQ")
                return
        
        try:
            queue = await self.channel.get_queue(self.queue_name)
            await queue.consume(self.process_message)
            logger.info(f"{self.service_name}: Started consuming messages from queue: {self.queue_name}")
        except Exception as e:
            logger.error(f"{self.service_name}: Failed to start consuming messages: {e}")
    
    async def stop_consuming(self) -> None:
        """
        Stop consuming messages
        """
        # The channel will be closed with the connection, so we just need to
        # ensure we disconnect properly
        await self.disconnect()
