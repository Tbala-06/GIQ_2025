"""
Test Data Generator for Road Painting Bot
Generates sample submissions for testing and demonstration
"""

import random
from datetime import datetime, timedelta
from database import get_db

# Sample locations (major cities with coordinates)
SAMPLE_LOCATIONS = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
    {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
    {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
    {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936},
    {"name": "San Diego", "lat": 32.7157, "lon": -117.1611},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
    {"name": "San Jose", "lat": 37.3382, "lon": -121.8863},
]

# Sample user data
SAMPLE_USERS = [
    {"user_id": 100001, "username": "john_doe", "first_name": "John", "last_name": "Doe"},
    {"user_id": 100002, "username": "jane_smith", "first_name": "Jane", "last_name": "Smith"},
    {"user_id": 100003, "username": "bob_wilson", "first_name": "Bob", "last_name": "Wilson"},
    {"user_id": 100004, "username": "alice_brown", "first_name": "Alice", "last_name": "Brown"},
    {"user_id": 100005, "username": "charlie_davis", "first_name": "Charlie", "last_name": "Davis"},
    {"user_id": 100006, "username": "emma_garcia", "first_name": "Emma", "last_name": "Garcia"},
    {"user_id": 100007, "username": "david_martinez", "first_name": "David", "last_name": "Martinez"},
    {"user_id": 100008, "username": "sophia_lopez", "first_name": "Sophia", "last_name": "Lopez"},
]

# Sample photo IDs (these are placeholder IDs - in real use, these would be actual Telegram file_ids)
SAMPLE_PHOTO_IDS = [
    "AgACAgIAAxkBAAIBY2ZxcHVnZGQwbGtqZGZhc2Rma2xqZGZhc2Rm",
    "AgACAgIAAxkBAAIBY2ZxcHVnZGQwbGtqZGZhc2Rma2xqZGZhc2Rn",
    "AgACAgIAAxkBAAIBY2ZxcHVnZGQwbGtqZGZhc2Rma2xqZGZhc2Ro",
    "AgACAgIAAxkBAAIBY2ZxcHVnZGQwbGtqZGZhc2Rma2xqZGZhc2Rp",
    "AgACAgIAAxkBAAIBY2ZxcHVnZGQwbGtqZGZhc2Rma2xqZGZhc2Rq",
]

# Inspector data
SAMPLE_INSPECTORS = [
    {"inspector_id": 200001, "username": "inspector_mike"},
    {"inspector_id": 200002, "username": "inspector_sarah"},
    {"inspector_id": 200003, "username": "inspector_tom"},
]

REJECTION_REASONS = [
    "Photo quality too low",
    "Location not precise enough",
    "Not a valid road damage",
    "Duplicate submission",
    "Already scheduled for repair"
]

# Sample descriptions
SAMPLE_DESCRIPTIONS = [
    "Large pothole about 2 meters wide, 30cm deep. Major safety concern.",
    "Severe road cracks extending 10 feet. Multiple vehicles damaged.",
    "Faded paint on crosswalk, barely visible. Dangerous for pedestrians.",
    "Deep potholes spanning 5 meters. Water accumulation during rain.",
    "Road surface deteriorating badly. Urgent repair needed.",
    "Minor cracks about 3 feet long. Not urgent but needs attention.",
    "Paint markings completely worn off. Difficult to see lanes at night.",
    "Massive pothole 4 meters wide. Cars swerving to avoid.",
    "Road damage from recent weather. Approximately 15 feet affected.",
    "Surface degradation near intersection. Safety hazard for bikes."
]


def add_random_offset(coord, max_offset=0.05):
    """Add random offset to coordinates to create variety"""
    return coord + random.uniform(-max_offset, max_offset)


def generate_test_data(num_submissions=20, num_pending=5, num_approved=10, num_rejected=5):
    """
    Generate test data with specified distribution

    Args:
        num_submissions: Total number of submissions to create
        num_pending: Number of pending submissions
        num_approved: Number of approved submissions
        num_rejected: Number of rejected submissions
    """
    db = get_db()

    # Adjust numbers if they don't match total
    total_requested = num_pending + num_approved + num_rejected
    if total_requested != num_submissions:
        num_submissions = total_requested

    print(f"Generating {num_submissions} test submissions...")
    print(f"  - Pending: {num_pending}")
    print(f"  - Approved: {num_approved}")
    print(f"  - Rejected: {num_rejected}")
    print()

    submissions_created = []

    # Create submissions with different statuses
    statuses = ['pending'] * num_pending + ['approved'] * num_approved + ['rejected'] * num_rejected
    random.shuffle(statuses)

    for i, status in enumerate(statuses, 1):
        # Random user
        user = random.choice(SAMPLE_USERS)

        # Random location with offset
        location = random.choice(SAMPLE_LOCATIONS)
        lat = add_random_offset(location['lat'])
        lon = add_random_offset(location['lon'])

        # Random photo
        photo_id = random.choice(SAMPLE_PHOTO_IDS)

        # Random description
        description = random.choice(SAMPLE_DESCRIPTIONS)

        # Random timestamp within last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        submission_time = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

        # Create submission manually in database
        import sqlite3
        from config import Config

        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO submissions
            (user_id, username, first_name, last_name, photo_id,
             latitude, longitude, description, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user['user_id'], user['username'], user['first_name'], user['last_name'],
              photo_id, lat, lon, description, submission_time, status))

        submission_id = cursor.lastrowid

        # If approved or rejected, add inspector data
        if status in ['approved', 'rejected']:
            inspector = random.choice(SAMPLE_INSPECTORS)
            decision_time = submission_time + timedelta(hours=random.randint(1, 48))
            rejection_reason = random.choice(REJECTION_REASONS) if status == 'rejected' else None
            notes = "Test approval" if status == 'approved' else None

            cursor.execute('''
                UPDATE submissions
                SET inspector_id = ?,
                    inspector_username = ?,
                    decision_timestamp = ?,
                    rejection_reason = ?,
                    notes = ?
                WHERE id = ?
            ''', (inspector['inspector_id'], inspector['username'], decision_time,
                  rejection_reason, notes, submission_id))

        conn.commit()
        conn.close()

        submissions_created.append({
            'id': submission_id,
            'status': status,
            'location': location['name']
        })

        print(f"✓ Created submission #{submission_id} - {status} - {location['name']}")

    print()
    print(f"✅ Successfully created {len(submissions_created)} test submissions!")
    print()
    print("You can now test the bot with:")
    print("  - /pending  (to review pending submissions)")
    print("  - /history  (to see approved/rejected submissions)")
    print("  - /stats    (to view statistics)")
    print()

    return submissions_created


def clear_all_data():
    """Clear all submissions from database (use with caution!)"""
    response = input("⚠️  WARNING: This will delete ALL submissions. Are you sure? (type 'yes' to confirm): ")

    if response.lower() != 'yes':
        print("❌ Operation cancelled")
        return

    from config import Config
    import sqlite3

    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM submissions')
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"✅ Deleted {deleted} submissions")


def show_statistics():
    """Show current database statistics"""
    db = get_db()
    stats = db.get_statistics()

    print()
    print("📊 Current Database Statistics")
    print("=" * 40)
    print(f"Total Submissions: {stats['total_submissions']}")
    print(f"Pending:           {stats['total_pending']}")
    print(f"Approved:          {stats['total_approved']}")
    print(f"Rejected:          {stats['total_rejected']}")
    print(f"Submitted Today:   {stats['today_submitted']}")
    print(f"Approved Today:    {stats['today_approved']}")

    if stats['total_submissions'] > 0:
        approval_rate = (stats['total_approved'] / stats['total_submissions']) * 100
        print(f"Approval Rate:     {approval_rate:.1f}%")

    print("=" * 40)
    print()


def main():
    """Main function for interactive test data generation"""
    print()
    print("=" * 60)
    print("Road Painting Bot - Test Data Generator")
    print("=" * 60)
    print()

    while True:
        print("Options:")
        print("1. Generate test data (default: 20 submissions)")
        print("2. Generate test data (custom)")
        print("3. Show current statistics")
        print("4. Clear all data (⚠️  WARNING)")
        print("5. Exit")
        print()

        choice = input("Enter your choice (1-5): ").strip()

        if choice == '1':
            generate_test_data()

        elif choice == '2':
            try:
                num_pending = int(input("Number of pending submissions: "))
                num_approved = int(input("Number of approved submissions: "))
                num_rejected = int(input("Number of rejected submissions: "))
                total = num_pending + num_approved + num_rejected
                generate_test_data(total, num_pending, num_approved, num_rejected)
            except ValueError:
                print("❌ Invalid input. Please enter numbers only.")

        elif choice == '3':
            show_statistics()

        elif choice == '4':
            clear_all_data()

        elif choice == '5':
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please try again.")

        print()


if __name__ == '__main__':
    main()
