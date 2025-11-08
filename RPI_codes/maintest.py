#!/usr/bin/env python3
"""
Main Test Script
================

Simple test script that:
1. Connects to MQTT broker
2. Listens for deploy commands
3. Displays received lat/long
4. Tests EV3 motor movements (forward and backward)

Usage:
    python3 maintest.py
    python3 maintest.py --simulate  # Test without hardware
"""

import time
import logging
import argparse
import sys
import os

# Add communication directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'communication'))

# Import MQTT client
try:
    from communication.mqtt_client import MQTTClient
    MQTT_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: MQTT client not found, using simple MQTT")
    MQTT_AVAILABLE = False
    import paho.mqtt.client as mqtt
    import json

# Import EV3 controller
from ev3_comm import EV3Controller

# Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC_DEPLOY = "giq/robot/deploy"
MQTT_TOPIC_STATUS = "giq/robot/status"

logger = logging.getLogger(__name__)


class SimpleRobotTest:
    """
    Simple robot test that listens for MQTT deploy commands
    and tests EV3 motor movements.
    """

    def __init__(self, simulate=False):
        """
        Initialize test.

        Args:
            simulate: If True, simulates EV3 without hardware
        """
        self.simulate = simulate
        self.running = False
        self.ev3 = None
        self.mqtt_client = None
        self.received_deploy = False

        print("\n" + "=" * 70)
        print("SIMPLE ROBOT TEST")
        print("=" * 70)
        print(f"Mode: {'SIMULATION' if simulate else 'HARDWARE'}")
        print(f"MQTT Broker: {MQTT_BROKER}")
        print(f"Deploy Topic: {MQTT_TOPIC_DEPLOY}")
        print("=" * 70 + "\n")

    def start(self):
        """Start the test"""
        try:
            # Connect to EV3
            print("→ Connecting to EV3...")
            self.ev3 = EV3Controller(simulate=self.simulate)
            if not self.ev3.connect():
                print("✗ EV3 connection failed")
                return False
            print("✓ EV3 connected\n")

            # Connect to MQTT
            print("→ Connecting to MQTT...")
            if not self._connect_mqtt():
                print("✗ MQTT connection failed")
                return False
            print("✓ MQTT connected\n")

            print("=" * 70)
            print("🎯 READY - Waiting for deploy command...")
            print(f"   Listening on: {MQTT_TOPIC_DEPLOY}")
            print("   Press Ctrl+C to exit")
            print("=" * 70 + "\n")

            self.running = True
            return True

        except Exception as e:
            print(f"✗ Startup failed: {e}")
            return False

    def _connect_mqtt(self):
        """Connect to MQTT broker"""
        if MQTT_AVAILABLE:
            # Use existing MQTT client
            self.mqtt_client = MQTTClient(client_id="robot_test")
            self.mqtt_client.on_deploy_command(self._on_deploy_received)
            return self.mqtt_client.connect()

        else:
            # Use simple MQTT client
            self.mqtt_client = mqtt.Client(client_id="robot_test")
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message

            try:
                self.mqtt_client.connect(MQTT_BROKER, 1883, 60)
                self.mqtt_client.loop_start()
                time.sleep(2)  # Wait for connection
                return True
            except Exception as e:
                print(f"MQTT connection error: {e}")
                return False

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print(f"  Subscribing to {MQTT_TOPIC_DEPLOY}...")
            client.subscribe(MQTT_TOPIC_DEPLOY)
        else:
            print(f"  Connection failed with code {rc}")

    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            self._on_deploy_received(data)
        except Exception as e:
            print(f"Error parsing message: {e}")

    def _on_deploy_received(self, data):
        """
        Handle deploy command received from MQTT.

        Args:
            data: Dictionary with deployment info
        """
        self.received_deploy = True

        print("\n" + "🎯" * 35)
        print("DEPLOY COMMAND RECEIVED!")
        print("🎯" * 35)

        # Extract coordinates
        job_id = data.get('job_id', 'unknown')
        latitude = data.get('latitude', 0.0)
        longitude = data.get('longitude', 0.0)

        # Display information
        print(f"\n📋 Deployment Information:")
        print(f"   Job ID:    {job_id}")
        print(f"   Latitude:  {latitude:.6f}")
        print(f"   Longitude: {longitude:.6f}")
        print("\n" + "=" * 70)

        # Test EV3 motors
        print("\n🤖 Testing EV3 Motors...")
        print("-" * 70)
        self._test_motors()

        print("\n" + "=" * 70)
        print("✅ TEST COMPLETE")
        print("=" * 70)
        print("\nWaiting for next deploy command...")
        print("(Press Ctrl+C to exit)\n")

    def _test_motors(self):
        """Test EV3 motor movements"""
        try:
            # Test 1: Move forward
            print("\n→ Test 1: Moving FORWARD 30cm...")
            result = self.ev3.move_forward(30, speed=40)
            if result:
                left_enc, right_enc = result
                print(f"   ✓ Forward complete")
                print(f"     Encoders: Left={left_enc}, Right={right_enc}")
            else:
                print(f"   ✗ Forward failed")

            # Wait
            print("\n   Waiting 2 seconds...")
            time.sleep(2)

            # Test 2: Move backward
            print("\n→ Test 2: Moving BACKWARD 30cm...")
            result = self.ev3.move_backward(30, speed=40)
            if result:
                left_enc, right_enc = result
                print(f"   ✓ Backward complete")
                print(f"     Encoders: Left={left_enc}, Right={right_enc}")
            else:
                print(f"   ✗ Backward failed")

            # Wait
            print("\n   Waiting 2 seconds...")
            time.sleep(2)

            # Test 3: Stop
            print("\n→ Test 3: Stopping motors...")
            self.ev3.stop()
            print(f"   ✓ Motors stopped")

            print("\n" + "-" * 70)
            print("✅ Motor test sequence complete!")
            print("-" * 70)

        except Exception as e:
            print(f"\n✗ Motor test error: {e}")
            import traceback
            traceback.print_exc()

    def run(self):
        """Main run loop"""
        if not self.start():
            return

        try:
            # Keep running until interrupted
            while self.running:
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")

        finally:
            self.stop()

    def stop(self):
        """Stop and cleanup"""
        print("\n→ Shutting down...")

        self.running = False

        # Stop EV3
        if self.ev3:
            print("  Stopping motors...")
            self.ev3.stop()
            print("  Disconnecting EV3...")
            self.ev3.disconnect()

        # Disconnect MQTT
        if self.mqtt_client:
            print("  Disconnecting MQTT...")
            if MQTT_AVAILABLE:
                self.mqtt_client.disconnect()
            else:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()

        print("✓ Shutdown complete\n")


# ============================================================================
# MQTT TEST PUBLISHER (FOR TESTING)
# ============================================================================

def test_publish_deploy(lat=1.3521, lon=103.8198, job_id=1):
    """
    Publish a test deploy command to MQTT.
    Use this to test the system without the Telegram bot.

    Args:
        lat: Latitude
        lon: Longitude
        job_id: Job identifier
    """
    import paho.mqtt.client as mqtt
    import json

    print("\n" + "=" * 70)
    print("PUBLISHING TEST DEPLOY COMMAND")
    print("=" * 70)

    client = mqtt.Client(client_id="test_publisher")

    try:
        print(f"→ Connecting to {MQTT_BROKER}...")
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_start()
        time.sleep(1)

        # Create deploy message
        message = {
            "job_id": job_id,
            "latitude": lat,
            "longitude": lon,
            "timestamp": time.time()
        }

        payload = json.dumps(message)

        print(f"→ Publishing to {MQTT_TOPIC_DEPLOY}...")
        print(f"   Message: {payload}")

        result = client.publish(MQTT_TOPIC_DEPLOY, payload, qos=1)
        result.wait_for_publish()

        print("✓ Deploy command published!")
        print("\nThe robot should receive this command shortly.")
        print("=" * 70 + "\n")

        client.loop_stop()
        client.disconnect()

    except Exception as e:
        print(f"✗ Publish failed: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Simple Robot Test')
    parser.add_argument('--simulate', action='store_true',
                       help='Run in simulation mode (no hardware)')
    parser.add_argument('--publish-test', action='store_true',
                       help='Publish a test deploy command and exit')
    parser.add_argument('--lat', type=float, default=1.3521,
                       help='Test latitude (default: 1.3521)')
    parser.add_argument('--lon', type=float, default=103.8198,
                       help='Test longitude (default: 103.8198)')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # If publish test mode, just send a test message
    if args.publish_test:
        test_publish_deploy(args.lat, args.lon)
        return

    # Run the test
    try:
        test = SimpleRobotTest(simulate=args.simulate)
        test.run()

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
