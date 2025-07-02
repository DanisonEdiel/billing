import json
import uuid
from datetime import datetime
from typing import Any, Dict

import aio_pika
from loguru import logger

from app.core.config import settings


class EventPublisher:
    """
    Event publisher for sending messages to RabbitMQ
    """
    def __init__(self):
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
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            
            # Declare exchanges
            await self.channel.declare_exchange(
                "billing_events", 
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            self.connected = True
            logger.info("Connected to RabbitMQ broker")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ broker: {e}")
            self.connected = False
    
    async def disconnect(self) -> None:
        """
        Disconnect from RabbitMQ broker
        """
        if self.connection and self.connected:
            await self.connection.close()
            self.connected = False
            logger.info("Disconnected from RabbitMQ broker")
    
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
            logger.info(f"Event published: {event['event_type']} with ID {event['event_id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    async def publish_invoice_created(self, invoice_data: Dict[str, Any], correlation_id: str = None) -> bool:
        """
        Publish an invoice created event
        """
        event_data = {
            "event_type": "invoice_created",
            "payload": {
                "invoice_id": invoice_data.get("id"),
                "customer_id": invoice_data.get("customer_id"),
                "amount": invoice_data.get("amount"),
                "tax_amount": invoice_data.get("tax_amount"),
                "discount_amount": invoice_data.get("discount_amount"),
                "total_amount": invoice_data.get("total_amount"),
                "status": invoice_data.get("status"),
                "created_at": invoice_data.get("created_at", datetime.utcnow().isoformat()),
                "due_date": invoice_data.get("due_date"),
                "user_id": invoice_data.get("user_id")
            }
        }
        
        return await self.publish_event("invoice.created", event_data, correlation_id)
    
    async def publish_invoice_updated(self, invoice_data: Dict[str, Any], correlation_id: str = None) -> bool:
        """
        Publish an invoice updated event
        """
        event_data = {
            "event_type": "invoice_updated",
            "payload": {
                "invoice_id": invoice_data.get("id"),
                "customer_id": invoice_data.get("customer_id"),
                "status": invoice_data.get("status"),
                "updated_at": datetime.utcnow().isoformat(),
                "user_id": invoice_data.get("user_id")
            }
        }
        
        return await self.publish_event("invoice.updated", event_data, correlation_id)


# Singleton instance
event_publisher = EventPublisher()
