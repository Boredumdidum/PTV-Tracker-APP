#!/usr/bin/env python3
"""
PTV Tracker Telegram Bot
A Telegram bot for tracking Victorian public transport (PTV) services.
Runs on Raspberry Pi using polling mode (no webhook needed).
"""

import os
import logging
import requests
import hmac
import hashlib
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
PTV_DEV_ID = os.environ.get('PTV_DEV_ID')
PTV_API_KEY = os.environ.get('PTV_API_KEY')

# PTV API Helper
def get_ptv_data(endpoint):
    """Fetch data from PTV API with HMAC signature"""
    timestamp = str(int(time.time()))
    path = f'/v3/{endpoint}'
    raw = f'{path}?devid={PTV_DEV_ID}&timestamp={timestamp}'
    
    signature = hmac.new(
        PTV_API_KEY.encode(),
        raw.encode(),
        hashlib.sha1
    ).hexdigest()
    
    url = f'https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}'
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"PTV API error: {e}")
        return None

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text(
        "Welcome to PTV Tracker!\n\n"
        "Commands:\n"
        "/status - Check next departures\n"
        "/routes - List train/tram/bus routes\n"
        "/help - Show all commands"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get status for a stop"""
    # Example: Get departures for Flinders Street Station (ID: 1071)
    data = get_ptv_data('departures/route_type/0/stop/1071')
    
    if data and 'departures' in data:
        departures = data['departures'][:5]  # Top 5
        msg = "🚂 Next departures from Flinders St:\n\n"
        
        for dep in departures:
            route = dep.get('route_id', 'Unknown')
            direction = dep.get('direction', 'Unknown')
            est = dep.get('estimated_departure_utc', 'N/A')
            msg += f"Route {route} → {direction}\n"
        
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Couldn't fetch data. Try again later.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await update.message.reply_text(
        "Available Commands:\n\n"
        "/start - Welcome message\n"
        "/status - Check departures\n"
        "/routes - List routes\n"
        "/help - This message"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# Main function
def main():
    # Build application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Run the bot (polling mode - no webhook needed)
    logger.info("Starting bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
