"""
User handlers for Road Painting Bot
Handles user commands and report submission flow
"""

import logging
import os
import tempfile
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from database import get_db
from datetime import datetime
from road_analyzer import analyze_road_photo

logger = logging.getLogger(__name__)

# Conversation states
PHOTO, LOCATION, CONFIRM = range(3)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

    welcome_message = f"""
Welcome to the Road Painting Robot Bot! 🤖🛣️

I'm here to help you report damaged roads that need painting or repair.

Available Commands:
/report - Report a damaged road (submit photo and location)
/status - Check status of your submissions
/help - Show this help message

Inspector Commands:
/inspector - Access inspector mode
/pending - View pending submissions
/history - View recent decisions

How it works:
1. Use /report to start a new report
2. Upload a photo of the damaged road
3. Share your location
4. I'll assign a unique ID to your submission
5. An inspector will review and approve/reject it
6. You'll receive a notification with the decision

Let's make our roads better together! 🚀
"""

    await update.message.reply_text(welcome_message)
    logger.info(f"User {user.id} ({user.username}) started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await start_command(update, context)


async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the report submission flow"""
    user = update.effective_user

    await update.message.reply_text(
        "📸 Let's report a damaged road!\n\n"
        "First, please send me a clear photo of the damaged road area.\n\n"
        "You can cancel this process anytime by typing /cancel"
    )

    logger.info(f"User {user.id} started report submission")
    return PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive photo from user"""
    user = update.effective_user
    photo = update.message.photo[-1]  # Get highest resolution photo

    # Store photo file_id in context
    context.user_data['photo_id'] = photo.file_id
    context.user_data['photo_size'] = photo.file_size

    # Send processing message
    processing_msg = await update.message.reply_text(
        "✅ Photo received!\n\n"
        "🔍 Analyzing road markings, please wait..."
    )

    # Download and analyze the photo
    road_type = "Unknown"
    road_details = ""
    try:
        # Download photo to temporary file
        file = await context.bot.get_file(photo.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            temp_path = tmp_file.name
            await file.download_to_drive(temp_path)

        # Analyze road markings
        logger.info(f"Analyzing road image: {temp_path}")
        analysis = await analyze_road_photo(temp_path)

        # Store analysis results
        context.user_data['road_type'] = analysis.road_type
        context.user_data['road_confidence'] = analysis.confidence
        context.user_data['road_details'] = analysis.details
        context.user_data['road_features'] = ", ".join(analysis.detected_features)

        road_type = analysis.road_type
        road_details = analysis.details

        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass

        logger.info(f"Road analysis complete: {road_type} ({analysis.confidence})")

    except Exception as e:
        logger.error(f"Error analyzing photo: {e}", exc_info=True)
        context.user_data['road_type'] = "Analysis Error"
        context.user_data['road_confidence'] = "N/A"
        context.user_data['road_details'] = "Could not analyze image"
        context.user_data['road_features'] = "none"

    # Delete processing message
    try:
        await processing_msg.delete()
    except:
        pass

    # Create keyboard with location button
    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Share Location", request_location=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    # Send result with location request
    analysis_emoji = {
        "HIGH": "✅",
        "MEDIUM": "⚠️",
        "LOW": "❓",
        "N/A": "❌"
    }.get(context.user_data.get('road_confidence', 'N/A'), '❓')

    await update.message.reply_text(
        f"✅ Photo received and analyzed!\n\n"
        f"🛣️ **Detected Road Type:**\n"
        f"{analysis_emoji} {road_type}\n"
        f"📊 Confidence: {context.user_data.get('road_confidence', 'N/A')}\n"
        f"📝 {road_details}\n\n"
        f"📍 Now, please share the location of this road.\n\n"
        f"You can tap the button below to share your current location, "
        f"or manually send a location from Telegram's location picker.\n\n"
        f"Type /cancel to cancel this report.",
        reply_markup=location_keyboard,
        parse_mode='Markdown'
    )

    logger.info(f"User {user.id} uploaded photo (file_id: {photo.file_id})")
    return LOCATION


async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive location from user"""
    user = update.effective_user
    location = update.message.location

    # Store location in context
    context.user_data['latitude'] = location.latitude
    context.user_data['longitude'] = location.longitude

    # Show confirmation with all details
    road_type = context.user_data.get('road_type', 'Unknown')
    road_confidence = context.user_data.get('road_confidence', 'N/A')
    road_details = context.user_data.get('road_details', 'No analysis available')

    # Confidence emoji
    confidence_emoji = {
        "HIGH": "✅",
        "MEDIUM": "⚠️",
        "LOW": "❓",
        "N/A": "❌"
    }.get(road_confidence, '❓')

    confirmation_message = (
        "📋 **Please confirm your submission:**\n\n"
        f"📸 Photo: Received ({context.user_data['photo_size']} bytes)\n\n"
        f"🛣️ **Detected Road Type:**\n"
        f"{confidence_emoji} {road_type}\n"
        f"📊 Confidence: {road_confidence}\n"
        f"📝 {road_details}\n\n"
        f"📍 **Location:** {location.latitude:.6f}, {location.longitude:.6f}\n\n"
        f"👤 **Submitted by:** {user.first_name or ''} {user.last_name or ''} (@{user.username or 'N/A'})\n"
        f"🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "✅ Type *yes* to submit\n"
        "❌ Type *no* to cancel"
    )

    await update.message.reply_text(
        confirmation_message,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )

    logger.info(f"User {user.id} shared location: {location.latitude}, {location.longitude}")
    return CONFIRM


async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and save submission"""
    user = update.effective_user
    response = update.message.text.lower()

    if response in ['yes', 'y', 'confirm', 'ok']:
        # Save to database
        db = get_db()
        try:
            submission_id = db.create_submission(
                user_id=user.id,
                username=user.username or '',
                first_name=user.first_name or '',
                last_name=user.last_name or '',
                photo_id=context.user_data['photo_id'],
                latitude=context.user_data['latitude'],
                longitude=context.user_data['longitude'],
                road_type=context.user_data.get('road_type'),
                road_confidence=context.user_data.get('road_confidence'),
                road_details=context.user_data.get('road_details'),
                road_features=context.user_data.get('road_features')
            )

            # Send confirmation with submission ID
            await update.message.reply_text(
                f"✅ Submission successful!\n\n"
                f"📝 Your submission ID: #{submission_id}\n\n"
                f"Your report has been submitted and is now pending inspector review.\n"
                f"You'll receive a notification once an inspector reviews your submission.\n\n"
                f"Use /status to check the status of your submissions.\n"
                f"Thank you for helping improve our roads! 🙏"
            )

            # Notify inspectors about new submission (if they're in a chat with the bot)
            # This would require storing inspector chat IDs or using a broadcast mechanism
            # For now, inspectors will see pending submissions when they check

            logger.info(f"Submission #{submission_id} created for user {user.id}")

        except Exception as e:
            logger.error(f"Error creating submission: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error saving your submission. Please try again later."
            )

        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            "❌ Submission cancelled.\n\n"
            "Use /report to start a new report."
        )
        context.user_data.clear()
        return ConversationHandler.END


async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the report submission"""
    await update.message.reply_text(
        "❌ Report cancelled.\n\n"
        "Use /report to start a new report anytime.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    logger.info(f"User {update.effective_user.id} cancelled report submission")
    return ConversationHandler.END


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's submission status"""
    user = update.effective_user
    db = get_db()

    try:
        submissions = db.get_user_submissions(user.id, limit=10)

        if not submissions:
            await update.message.reply_text(
                "📭 You haven't submitted any reports yet.\n\n"
                "Use /report to submit your first road damage report!"
            )
            return

        # Format submissions
        status_message = f"📊 Your Submissions (Last {len(submissions)}):\n\n"

        for sub in submissions:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }.get(sub['status'], '❓')

            timestamp = datetime.fromisoformat(sub['timestamp']).strftime('%Y-%m-%d %H:%M')

            status_message += f"{status_emoji} Submission #{sub['id']}\n"
            status_message += f"   Status: {sub['status'].upper()}\n"
            status_message += f"   Submitted: {timestamp}\n"

            if sub['status'] == 'approved':
                decision_time = datetime.fromisoformat(sub['decision_timestamp']).strftime('%Y-%m-%d %H:%M')
                status_message += f"   Approved: {decision_time}\n"
                if sub['notes']:
                    status_message += f"   Notes: {sub['notes']}\n"

            elif sub['status'] == 'rejected':
                decision_time = datetime.fromisoformat(sub['decision_timestamp']).strftime('%Y-%m-%d %H:%M')
                status_message += f"   Rejected: {decision_time}\n"
                if sub['rejection_reason']:
                    status_message += f"   Reason: {sub['rejection_reason']}\n"

            status_message += "\n"

        await update.message.reply_text(status_message)
        logger.info(f"User {user.id} checked status")

    except Exception as e:
        logger.error(f"Error fetching user status: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error fetching your submissions."
        )


# Create conversation handler
def get_report_conversation_handler():
    """Create and return the conversation handler for report submission"""
    return ConversationHandler(
        entry_points=[CommandHandler('report', report_start)],
        states={
            PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c:
                              u.message.reply_text("Please send a photo of the damaged road."))
            ],
            LOCATION: [
                MessageHandler(filters.LOCATION, receive_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c:
                              u.message.reply_text("Please share your location using the button below."))
            ],
            CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_submission)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_report)],
        name="report_conversation",
        persistent=False
    )
