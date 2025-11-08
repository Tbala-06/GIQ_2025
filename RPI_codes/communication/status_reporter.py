#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Status Reporter Module
Background thread for periodic status reporting via MQTT.
"""

import threading
import time
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class StatusReporter:
    """Periodic status reporting via MQTT"""

    def __init__(self, mqtt_client):
        """
        Initialize Status Reporter.

        Args:
            mqtt_client: MQTTClient instance for publishing
        """
        self.mqtt = mqtt_client
        self.running = False
        self.thread = None
        self.interval = 10.0  # Default report interval

        # Current status data
        self.current_status = "idle"
        self.current_lat = None
        self.current_lon = None
        self.current_battery = None
        self.current_job_id = None
        self.additional_data = {}

        logger.info("Status Reporter initialized")

    def start_reporting(self, interval_seconds: float = 10.0):
        """
        Start periodic status reporting.

        Args:
            interval_seconds: Time between status reports
        """
        if self.running:
            logger.warning("Status reporter already running")
            return

        self.interval = interval_seconds
        self.running = True

        self.thread = threading.Thread(target=self._reporting_loop, daemon=True)
        self.thread.start()

        logger.info(f"Status reporting started (interval: {interval_seconds}s)")

    def stop_reporting(self):
        """Stop status reporting thread"""
        if not self.running:
            return

        logger.info("Stopping status reporter...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning("Status reporter thread did not stop gracefully")

        logger.info("Status reporter stopped")

    def update_status(self, status: str):
        """
        Update current status and send immediate update.

        Args:
            status: New status string
        """
        if self.current_status != status:
            logger.info(f"Status changed: {self.current_status} → {status}")
            self.current_status = status
            self.force_update()

    def update_position(self, lat: float, lon: float):
        """
        Update current position.

        Args:
            lat: Current latitude
            lon: Current longitude
        """
        self.current_lat = lat
        self.current_lon = lon
        logger.debug(f"Position updated: ({lat:.6f}, {lon:.6f})")

    def update_battery(self, battery_level: int):
        """
        Update battery level.

        Args:
            battery_level: Battery percentage (0-100)
        """
        self.current_battery = max(0, min(100, battery_level))
        logger.debug(f"Battery updated: {self.current_battery}%")

    def set_current_job(self, job_id: Optional[int]):
        """
        Set current job ID.

        Args:
            job_id: Job ID or None if no active job
        """
        self.current_job_id = job_id
        if job_id:
            logger.info(f"Current job: {job_id}")
        else:
            logger.info("No active job")

    def set_additional_data(self, **kwargs):
        """
        Set additional data to include in status updates.

        Args:
            **kwargs: Key-value pairs to add to status messages
        """
        self.additional_data.update(kwargs)

    def report_error(self, error_message: str):
        """
        Report error status immediately.

        Args:
            error_message: Error description
        """
        logger.error(f"Reporting error: {error_message}")
        self.current_status = "error"
        self.additional_data['error'] = error_message
        self.force_update()

    def force_update(self):
        """Send immediate status update"""
        self._send_status()

    def _reporting_loop(self):
        """Background thread for periodic reporting"""
        logger.info("Status reporting loop started")

        while self.running:
            try:
                # Send status update
                self._send_status()

                # Sleep until next report (with interruptible checks)
                sleep_time = 0
                while sleep_time < self.interval and self.running:
                    time.sleep(0.5)
                    sleep_time += 0.5

            except Exception as e:
                logger.error(f"Error in reporting loop: {e}")
                time.sleep(1.0)

        logger.info("Status reporting loop ended")

    def _send_status(self):
        """Send current status via MQTT"""
        try:
            # Prepare additional data
            extra = dict(self.additional_data)

            # Add job ID if active
            if self.current_job_id:
                extra['job_id'] = self.current_job_id

            # Publish status
            success = self.mqtt.publish_status(
                status=self.current_status,
                lat=self.current_lat,
                lon=self.current_lon,
                battery=self.current_battery,
                additional_data=extra if extra else None
            )

            if not success:
                logger.warning("Failed to send status update")

        except Exception as e:
            logger.error(f"Error sending status: {e}")
