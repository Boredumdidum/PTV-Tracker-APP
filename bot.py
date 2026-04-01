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
        "/search <stop name> - Find a stop ID\n"
        "/help - Show all commands"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for stops by name"""
    # Get search term from command arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /search <stop name>\n"
            "Example: /search Flinders Street\n"
            "Example: /search South Yarra"
        )
        return
    
    search_term = ' '.join(context.args)
    logger.info(f"Searching for: {search_term}")
    
    # Call PTV search API
    data = get_ptv_data(f'search/{search_term}')
    
    if data and 'stops' in data and data['stops']:
        stops = data['stops'][:5]  # Limit to 5 results
        msg = f"🔍 Search results for '{search_term}':\n\n"
        
        for stop in stops:
            stop_name = stop.get('stop_name', 'Unknown')
            stop_id = stop.get('stop_id', 'Unknown')
            route_type = stop.get('route_type', 0)
            route_type_name = {0: '🚂 Train', 1: '🚃 Tram', 2: '🚌 Bus', 3: '🚆 VLine', 4: '🌙 Night Bus'}.get(route_type, 'Unknown')
            
            msg += f"{route_type_name} Stop ID: `{stop_id}`\n"
            msg += f"Name: {stop_name}\n\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"❌ No stops found for '{search_term}'.\n"
            "Try:\n"
            "- Check spelling\n"
            "- Use a simpler name (e.g., 'Flinders' instead of 'Flinders Street Railway Station')\n"
            "- Try a nearby major station"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await update.message.reply_text(
        "Available Commands:\n\n"
        "/search <name> - Find stops (e.g., /search Flinders)\n"
        "/start - Welcome message\n"
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
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("help", help_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Run the bot (polling mode - no webhook needed)
    logger.info("Starting bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
