#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Deploy Command Sender
===========================

Simple script to send MQTT deploy commands for testing.
Use this to test the robot without needing the full Telegram bot.

Usage:
    # Send default test coordinates
    python3 send_test_deploy.py

    # Send custom coordinates
    python3 send_test_deploy.py --lat 1.3521 --lon 103.8198

    # Send with custom job ID
    python3 send_test_deploy.py --job-id 42
"""

import paho.mqtt.client as mqtt
import json
import time
import argparse

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "giq/robot/deploy"


def send_deploy_command(latitude, longitude, job_id=None):
    """
    Send deploy command via MQTT.

    Args:
        latitude: Target latitude
        longitude: Target longitude
        job_id: Optional job identifier
    """
    if job_id is None:
        job_id = int(time.time())  # Use timestamp as job ID

    print("\n" + "=" * 70)
    print("SENDING DEPLOY COMMAND")
    print("=" * 70)
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Topic: {MQTT_TOPIC}")
    print("-" * 70)

    # Create MQTT client
    client_id = f"deploy_sender_{int(time.time())}"
    client = mqtt.Client(client_id=client_id)

    try:
        # Connect to broker
        print(f"\n→ Connecting to broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(2)  # Give it time to connect

        print("✓ Connected")

        # Create deploy message
        message = {
            "job_id": job_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": time.time(),
            "command": "DEPLOY"
        }

        payload = json.dumps(message, indent=2)

        # Display message
        print(f"\n→ Publishing message:")
        print("-" * 70)
        print(payload)
        print("-" * 70)

        # Publish
        result = client.publish(MQTT_TOPIC, payload, qos=1)
        result.wait_for_publish()

        print("\n✅ DEPLOY COMMAND SENT!")
        print("=" * 70)
        print(f"\n📍 Deployment Details:")
        print(f"   Job ID:    {job_id}")
        print(f"   Latitude:  {latitude:.6f}")
        print(f"   Longitude: {longitude:.6f}")
        print("\n" + "=" * 70)
        print("\n✓ The robot should receive this command shortly.")
        print("  Make sure maintest.py is running to see it!\n")

        # Cleanup
        time.sleep(1)
        client.loop_stop()
        client.disconnect()

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Send test deploy command via MQTT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send default coordinates
  python3 send_test_deploy.py

  # Send custom coordinates
  python3 send_test_deploy.py --lat 1.3521 --lon 103.8198

  # Send with custom job ID
  python3 send_test_deploy.py --lat 1.3521 --lon 103.8198 --job-id 42
        """
    )

    parser.add_argument('--lat', '--latitude', type=float, default=1.3521,
                       help='Target latitude (default: 1.3521)')
    parser.add_argument('--lon', '--longitude', type=float, default=103.8198,
                       help='Target longitude (default: 103.8198)')
    parser.add_argument('--job-id', type=int, default=None,
                       help='Job ID (default: current timestamp)')

    args = parser.parse_args()

    # Send the command
    send_deploy_command(args.lat, args.lon, args.job_id)


if __name__ == "__main__":
    main()
