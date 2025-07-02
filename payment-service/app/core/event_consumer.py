import asyncio
import json
from typing import Dict, Any, Callable, Awaitable

import aio_pika
from loguru import logger

from app.core.config import settings


class EventConsumer:
    """
    Event consumer for receiving messages from RabbitMQ
    """
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connected = False
        self.queue_name = "payment_service_queue"
        self.event_handlers = {}
    
    async def connect(self) -> None:
        """
        Connect to RabbitMQ broker
        """
        if self.connected:
            return
        
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
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
            
            # Bind queue to exchange with routing keys
            await queue.bind(exchange, routing_key="invoice.created")
            await queue.bind(exchange, routing_key="invoice.updated")
            
            self.connected = True
            logger.info("Connected to RabbitMQ broker as consumer")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ broker as consumer: {e}")
            self.connected = False
    
    async def disconnect(self) -> None:
        """
        Disconnect from RabbitMQ broker
        """
        if self.connection and self.connected:
            await self.connection.close()
            self.connected = False
            logger.info("Disconnected from RabbitMQ broker as consumer")
    
    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Register a handler for a specific event type
        """
        self.event_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
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
                    logger.info(f"Processing {event_type} event with ID {body.get('event_id')}")
                    await self.event_handlers[event_type](body)
                else:
                    logger.warning(f"No handler for event type: {event_type}")
            except json.JSONDecodeError:
                logger.error("Failed to decode message body as JSON")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def start_consuming(self) -> None:
        """
        Start consuming messages
        """
        if not self.connected:
            await self.connect()
            if not self.connected:
                logger.error("Cannot start consuming, not connected to RabbitMQ")
                return
        
        try:
            queue = await self.channel.get_queue(self.queue_name)
            await queue.consume(self.process_message)
            logger.info(f"Started consuming messages from queue: {self.queue_name}")
        except Exception as e:
            logger.error(f"Failed to start consuming messages: {e}")
    
    async def stop_consuming(self) -> None:
        """
        Stop consuming messages
        """
        # The channel will be closed with the connection, so we just need to
        # ensure we disconnect properly
        pass


# Create singleton instance
event_consumer = EventConsumer()

# Import handlers at the bottom to avoid circular imports
from app.services.payment_service import handle_invoice_created

# Register handlers
event_consumer.register_handler("invoice_created", handle_invoice_created)
