"""
Inspector handlers for Road Painting Bot
Handles inspector commands and approval/rejection flow
"""

import logging
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import get_db
from config import Config
from datetime import datetime

# Add RPI_codes to path for robot controller
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RPI_codes'))

logger = logging.getLogger(__name__)

# Global robot controller (initialized in robot_handlers.py)
from handlers.robot_handlers import robot_controller


async def inspector_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /inspector command - Show inspector dashboard"""
    user = update.effective_user

    # Check if user is authorized inspector
    if not Config.is_inspector(user.id):
        await update.message.reply_text(
            "🚫 Access Denied\n\n"
            "You are not authorized to access inspector mode.\n"
            "If you believe this is an error, please contact the administrator."
        )
        logger.warning(f"Unauthorized inspector access attempt by user {user.id}")
        return

    db = get_db()
    stats = db.get_statistics()

    dashboard_message = (
        "🔍 Inspector Dashboard\n\n"
        f"📊 Statistics:\n"
        f"   • Pending: {stats['total_pending']}\n"
        f"   • Approved (Total): {stats['total_approved']}\n"
        f"   • Rejected (Total): {stats['total_rejected']}\n"
        f"   • Total Submissions: {stats['total_submissions']}\n"
        f"   • Approved Today: {stats['today_approved']}\n\n"
        "📋 Commands:\n"
        "/pending - Review pending submissions\n"
        "/history - View recent decisions\n"
        "/stats - Show detailed statistics\n"
        "/export - Export all submissions to CSV\n\n"
        f"👤 Inspector: {user.first_name} (@{user.username or 'N/A'})"
    )

    await update.message.reply_text(dashboard_message)
    logger.info(f"Inspector {user.id} accessed dashboard")


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending submissions for review"""
    user = update.effective_user

    # Check authorization
    if not Config.is_inspector(user.id):
        await update.message.reply_text("🚫 Access Denied. Inspector authorization required.")
        return

    db = get_db()
    pending_submissions = db.get_pending_submissions(limit=10)

    if not pending_submissions:
        await update.message.reply_text(
            "✅ No pending submissions!\n\n"
            "All reports have been reviewed. Great job! 🎉"
        )
        return

    await update.message.reply_text(
        f"📋 Found {len(pending_submissions)} pending submission(s).\n"
        "Showing them one by one...\n"
    )

    # Show each pending submission
    for submission in pending_submissions:
        await show_submission_for_review(update, context, submission)

    logger.info(f"Inspector {user.id} viewed {len(pending_submissions)} pending submissions")


async def show_submission_for_review(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     submission: dict):
    """Display a single submission with approve/reject buttons"""
    # Format submission details
    timestamp = datetime.fromisoformat(submission['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

    caption = (
        f"📝 Submission #{submission['id']}\n\n"
        f"👤 User: {submission['first_name']} {submission['last_name']}\n"
        f"   Username: @{submission['username'] or 'N/A'}\n"
        f"   User ID: {submission['user_id']}\n\n"
        f"📍 Location:\n"
        f"   Lat: {submission['latitude']:.6f}\n"
        f"   Lon: {submission['longitude']:.6f}\n\n"
        f"🕐 Submitted: {timestamp}\n"
        f"📊 Status: {submission['status'].upper()}"
    )

    # Create inline keyboard with approve/reject buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve & Deploy", callback_data=f"approve_{submission['id']}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{submission['id']}")
        ],
        [
            InlineKeyboardButton("📍 View on Map", callback_data=f"map_{submission['id']}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send photo with caption and buttons
    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=submission['photo_id'],
            caption=caption,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending photo for submission {submission['id']}: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{caption}\n\n⚠️ Error loading photo",
            reply_markup=reply_markup
        )


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/rejection button callbacks"""
    query = update.callback_query
    user = update.effective_user

    # Check authorization
    if not Config.is_inspector(user.id):
        await query.answer("🚫 Access Denied", show_alert=True)
        return

    await query.answer()  # Acknowledge the callback

    # Parse callback data
    action, submission_id = query.data.split('_')
    submission_id = int(submission_id)

    db = get_db()
    submission = db.get_submission(submission_id)

    if not submission:
        await query.edit_message_caption(
            caption=f"❌ Error: Submission #{submission_id} not found."
        )
        return

    if submission['status'] != 'pending':
        await query.edit_message_caption(
            caption=f"⚠️ Submission #{submission_id} has already been {submission['status']}."
        )
        return

    if action == 'approve':
        # Approve submission
        db.update_submission_status(
            submission_id=submission_id,
            status='approved',
            inspector_id=user.id,
            inspector_username=user.username or '',
            notes='Approved for robot deployment'
        )

        # Update message
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n"
                    f"✅ APPROVED by {user.first_name} (@{user.username or 'N/A'})\n"
                    f"🤖 Robot deployment initiated!"
        )

        # Deploy robot to approved location
        try:
            if robot_controller:
                # Deploy robot with GPS coordinates
                robot_controller.deploy_mission(
                    target_lat=submission['latitude'],
                    target_lon=submission['longitude'],
                    mission_id=f"job_{submission_id}"
                )
                logger.info(f"🤖 Robot deployed to ({submission['latitude']:.6f}, {submission['longitude']:.6f})")
            else:
                logger.warning("Robot controller not available - deployment skipped")
        except Exception as e:
            logger.error(f"Error deploying robot: {e}")

        # Notify the original user
        try:
            await context.bot.send_message(
                chat_id=submission['user_id'],
                text=f"✅ Great news!\n\n"
                     f"Your submission #{submission_id} has been approved!\n"
                     f"The road painting robot will be deployed to this location.\n\n"
                     f"Thank you for helping improve our roads! 🙏"
            )
        except Exception as e:
            logger.error(f"Error notifying user {submission['user_id']}: {e}")

        logger.info(f"Submission #{submission_id} approved by inspector {user.id}")

    elif action == 'reject':
        # Reject submission
        db.update_submission_status(
            submission_id=submission_id,
            status='rejected',
            inspector_id=user.id,
            inspector_username=user.username or '',
            rejection_reason='Rejected by inspector'
        )

        # Update message
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n"
                    f"❌ REJECTED by {user.first_name} (@{user.username or 'N/A'})"
        )

        # Notify the original user
        try:
            await context.bot.send_message(
                chat_id=submission['user_id'],
                text=f"❌ Update on your submission\n\n"
                     f"Your submission #{submission_id} has been reviewed and rejected.\n"
                     f"This may be due to unclear photo, incorrect location, or other factors.\n\n"
                     f"You can submit a new report with /report if needed."
            )
        except Exception as e:
            logger.error(f"Error notifying user {submission['user_id']}: {e}")

        logger.info(f"Submission #{submission_id} rejected by inspector {user.id}")

    elif action == 'map':
        # Show location on map
        await context.bot.send_location(
            chat_id=update.effective_chat.id,
            latitude=submission['latitude'],
            longitude=submission['longitude']
        )
        await query.answer("📍 Location sent", show_alert=False)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent inspection decisions"""
    user = update.effective_user

    # Check authorization
    if not Config.is_inspector(user.id):
        await update.message.reply_text("🚫 Access Denied. Inspector authorization required.")
        return

    db = get_db()
    recent_decisions = db.get_recent_decisions(limit=15)

    if not recent_decisions:
        await update.message.reply_text("📭 No decisions recorded yet.")
        return

    history_message = f"📚 Recent Decisions (Last {len(recent_decisions)}):\n\n"

    for decision in recent_decisions:
        status_emoji = '✅' if decision['status'] == 'approved' else '❌'
        timestamp = datetime.fromisoformat(decision['decision_timestamp']).strftime('%Y-%m-%d %H:%M')

        history_message += (
            f"{status_emoji} Submission #{decision['id']}\n"
            f"   Status: {decision['status'].upper()}\n"
            f"   Inspector: @{decision['inspector_username'] or 'N/A'}\n"
            f"   Decision: {timestamp}\n"
            f"   User: @{decision['username'] or 'N/A'}\n\n"
        )

    await update.message.reply_text(history_message)
    logger.info(f"Inspector {user.id} viewed decision history")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics"""
    user = update.effective_user

    # Check authorization
    if not Config.is_inspector(user.id):
        await update.message.reply_text("🚫 Access Denied. Inspector authorization required.")
        return

    db = get_db()
    stats = db.get_statistics()

    stats_message = (
        "📊 Detailed Statistics\n\n"
        "📋 Overall:\n"
        f"   • Total Submissions: {stats['total_submissions']}\n"
        f"   • Pending Review: {stats['total_pending']}\n"
        f"   • Approved: {stats['total_approved']}\n"
        f"   • Rejected: {stats['total_rejected']}\n\n"
        "📅 Today:\n"
        f"   • Submitted Today: {stats['today_submitted']}\n"
        f"   • Approved Today: {stats['today_approved']}\n\n"
        "📈 Performance:\n"
    )

    if stats['total_submissions'] > 0:
        approval_rate = (stats['total_approved'] / stats['total_submissions']) * 100
        stats_message += f"   • Approval Rate: {approval_rate:.1f}%\n"

    stats_message += f"\n🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    await update.message.reply_text(stats_message)
    logger.info(f"Inspector {user.id} viewed statistics")


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export submissions to CSV"""
    user = update.effective_user

    # Check authorization
    if not Config.is_inspector(user.id):
        await update.message.reply_text("🚫 Access Denied. Inspector authorization required.")
        return

    await update.message.reply_text("📥 Exporting submissions to CSV...")

    try:
        db = get_db()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'submissions_{timestamp}.csv'
        filepath = db.export_to_csv(filename)

        if filepath:
            # Send the CSV file
            with open(filepath, 'rb') as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    filename=filename,
                    caption=f"✅ Export complete!\n\n"
                            f"📁 File: {filename}\n"
                            f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            logger.info(f"Inspector {user.id} exported submissions to {filename}")
        else:
            await update.message.reply_text("❌ No submissions to export.")

    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        await update.message.reply_text("❌ Error exporting submissions. Please try again later.")


def get_inspector_handlers():
    """Return list of inspector command handlers"""
    return [
        # Callback query handler for approval buttons
        CallbackQueryHandler(handle_approval_callback, pattern=r'^(approve|reject|map)_\d+$')
    ]
