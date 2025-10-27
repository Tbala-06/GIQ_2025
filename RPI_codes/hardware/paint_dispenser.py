#!/usr/bin/env python3
"""
Paint Dispenser Controller
Controls paint/sand dispensing mechanism via GPIO
"""

import time
from typing import Optional

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("WARNING: RPi.GPIO not available, running in simulation mode")

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class PaintDispenser:
    """Control paint/sand dispensing mechanism"""
    
    def __init__(self, simulate=False):
        """
        Initialize paint dispenser
        
        Args:
            simulate: If True, run in simulation mode without GPIO
        """
        self.simulate = simulate or not GPIO_AVAILABLE
        self.dispensing = False
        self.total_dispense_time = 0.0
        
        if not self.simulate:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(Config.PAINT_DISPENSER_PIN, GPIO.OUT)
            GPIO.output(Config.PAINT_DISPENSER_PIN, GPIO.LOW)
            
            logger.info("Paint dispenser initialized (GPIO mode)")
        else:
            logger.info("Paint dispenser initialized (SIMULATION mode)")
    
    def start_dispensing(self):
        """Start dispensing paint/sand"""
        if self.dispensing:
            logger.warning("Dispenser already running")
            return
        
        logger.info("Starting paint dispensing")
        
        if not self.simulate:
            GPIO.output(Config.PAINT_DISPENSER_PIN, GPIO.HIGH)
        
        self.dispensing = True
        self.dispense_start_time = time.time()
    
    def stop_dispensing(self):
        """Stop dispensing paint/sand"""
        if not self.dispensing:
            return
        
        logger.info("Stopping paint dispensing")
        
        if not self.simulate:
            GPIO.output(Config.PAINT_DISPENSER_PIN, GPIO.LOW)
        
        self.dispensing = False
        
        # Update total dispense time
        if hasattr(self, 'dispense_start_time'):
            duration = time.time() - self.dispense_start_time
            self.total_dispense_time += duration
            logger.info(f"Dispensed for {duration:.1f} seconds")
    
    def dispense(self, duration_seconds: float = None):
        """
        Dispense paint/sand for specified duration
        
        Args:
            duration_seconds: How long to dispense (uses config default if None)
        """
        if duration_seconds is None:
            duration_seconds = Config.PAINT_DISPENSE_DURATION
        
        logger.info(f"Dispensing paint for {duration_seconds:.1f} seconds")
        
        self.start_dispensing()
        time.sleep(duration_seconds)
        self.stop_dispensing()
    
    def pulse_dispense(self, pulse_duration: float = 0.1, pulses: int = 5, 
                      interval: float = 0.1):
        """
        Dispense in pulses (for better control/testing)
        
        Args:
            pulse_duration: Duration of each pulse in seconds
            pulses: Number of pulses
            interval: Time between pulses in seconds
        """
        logger.info(f"Pulse dispensing: {pulses} pulses of {pulse_duration}s")
        
        for i in range(pulses):
            self.start_dispensing()
            time.sleep(pulse_duration)
            self.stop_dispensing()
            
            if i < pulses - 1:  # Don't wait after last pulse
                time.sleep(interval)
    
    def is_dispensing(self) -> bool:
        """
        Check if currently dispensing
        
        Returns:
            True if dispensing, False otherwise
        """
        return self.dispensing
    
    def get_total_dispense_time(self) -> float:
        """
        Get total time spent dispensing since initialization
        
        Returns:
            Total dispense time in seconds
        """
        current_duration = 0.0
        if self.dispensing and hasattr(self, 'dispense_start_time'):
            current_duration = time.time() - self.dispense_start_time
        
        return self.total_dispense_time + current_duration
    
    def test_dispenser(self):
        """
        Test dispenser with a short pulse
        Useful for calibration and verification
        """
        logger.info("Testing dispenser")
        self.dispense(duration_seconds=0.5)
        logger.info("Dispenser test complete")
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        logger.info("Cleaning up paint dispenser")
        
        # Ensure dispenser is stopped
        if self.dispensing:
            self.stop_dispensing()
        
        if not self.simulate:
            GPIO.output(Config.PAINT_DISPENSER_PIN, GPIO.LOW)
            GPIO.cleanup([Config.PAINT_DISPENSER_PIN])