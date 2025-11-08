#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT Client Module
Handles MQTT communication with bot server for commands and status updates.
"""

import json
import time
from typing import Callable, Optional
import paho.mqtt.client as mqtt
from utils.logger import get_logger
from config import Config

logger = get_logger(__name__)


class MQTTClient:
    """MQTT client for robot communication"""

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialize MQTT Client.

        Args:
            client_id: Unique client ID (defaults to ROBOT_ID from config)
        """
        self.client_id = client_id or Config.ROBOT_ID
        self.client = mqtt.Client(client_id=self.client_id)
        self.connected = False
        self.deploy_callback = None

        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Set credentials if provided
        if Config.MQTT_USERNAME and Config.MQTT_PASSWORD:
            self.client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)

        logger.info(f"MQTT Client initialized (ID: {self.client_id})")

    def connect(self, retry_count: int = 3, retry_delay: float = 5.0) -> bool:
        """
        Connect to MQTT broker.

        Args:
            retry_count: Number of connection attempts
            retry_delay: Delay between retries (seconds)

        Returns:
            True if connected, False otherwise
        """
        logger.info(f"Connecting to MQTT broker: {Config.MQTT_BROKER}:{Config.MQTT_PORT}")

        for attempt in range(retry_count):
            try:
                self.client.connect(
                    Config.MQTT_BROKER,
                    Config.MQTT_PORT,
                    keepalive=60
                )

                # Start network loop in background
                self.client.loop_start()

                # Wait for connection
                timeout = 10.0
                start_time = time.time()
                while not self.connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)

                if self.connected:
                    logger.info("✅ MQTT connected successfully")
                    return True
                else:
                    logger.warning(f"Connection timeout (attempt {attempt + 1}/{retry_count})")

            except Exception as e:
                logger.error(f"Connection failed (attempt {attempt + 1}/{retry_count}): {e}")

            if attempt < retry_count - 1:
                logger.info(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

        logger.error("Failed to connect to MQTT broker")
        return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        logger.info("Disconnecting from MQTT broker")
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def on_deploy_command(self, callback: Callable):
        """
        Register callback for deploy commands.

        Args:
            callback: Function to call when deploy command received
                     Should accept dict with job_id, latitude, longitude
        """
        self.deploy_callback = callback
        logger.info("Deploy command callback registered")

    def publish_status(self, status: str, lat: Optional[float] = None,
                      lon: Optional[float] = None, battery: Optional[int] = None,
                      additional_data: Optional[dict] = None) -> bool:
        """
        Publish robot status to MQTT.

        Args:
            status: Robot status (idle, moving, positioning, painting, completed, error)
            lat: Current latitude
            lon: Current longitude
            battery: Battery level (0-100)
            additional_data: Additional data to include in message

        Returns:
            True if published successfully
        """
        try:
            message = {
                "robot_id": Config.ROBOT_ID,
                "status": status,
                "timestamp": time.time()
            }

            if lat is not None and lon is not None:
                message["lat"] = lat
                message["lng"] = lon

            if battery is not None:
                message["battery"] = battery

            if additional_data:
                message.update(additional_data)

            payload = json.dumps(message)
            result = self.client.publish(
                Config.MQTT_TOPIC_STATUS,
                payload,
                qos=1,
                retain=False
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Status published: {status}")
                return True
            else:
                logger.warning(f"Failed to publish status: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing status: {e}")
            return False

    def publish_job_complete(self, job_id: int, success: bool, message: str) -> bool:
        """
        Publish job completion message.

        Args:
            job_id: Job ID that completed
            success: Whether job completed successfully
            message: Completion message

        Returns:
            True if published successfully
        """
        try:
            payload = json.dumps({
                "robot_id": Config.ROBOT_ID,
                "job_id": job_id,
                "success": success,
                "message": message,
                "timestamp": time.time()
            })

            result = self.client.publish(
                Config.MQTT_TOPIC_COMPLETE,
                payload,
                qos=1,
                retain=False
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Job completion published: job_id={job_id}, success={success}")
                return True
            else:
                logger.warning(f"Failed to publish job completion: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing job completion: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to MQTT broker"""
        return self.connected

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT broker connected")

            # Subscribe to command topic
            client.subscribe(Config.MQTT_TOPIC_COMMANDS, qos=1)
            logger.info(f"Subscribed to: {Config.MQTT_TOPIC_COMMANDS}")
        else:
            self.connected = False
            logger.error(f"Connection failed with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect (code: {rc}), will reconnect")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            logger.debug(f"Message received on {topic}: {payload}")

            # Parse JSON payload
            data = json.loads(payload)

            # Handle deploy commands
            if topic == Config.MQTT_TOPIC_COMMANDS:
                self._handle_deploy_command(data)
            else:
                logger.warning(f"Unknown topic: {topic}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _handle_deploy_command(self, data: dict):
        """Handle deploy command from bot server"""
        logger.info(f"Deploy command received: {data}")

        # Validate required fields
        required_fields = ['job_id', 'latitude', 'longitude']
        if not all(field in data for field in required_fields):
            logger.error(f"Invalid deploy command: missing required fields")
            return

        # Call registered callback
        if self.deploy_callback:
            try:
                self.deploy_callback(data)
            except Exception as e:
                logger.error(f"Error in deploy callback: {e}")
        else:
            logger.warning("Deploy command received but no callback registered")
