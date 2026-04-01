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
import urllib.parse
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler,
    MessageHandler, filters
)
from datetime import datetime
from zoneinfo import ZoneInfo

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

# Conversation states
ASKING_ROUTE_TYPE = 1

# Route types table
ROUTE_TYPES = [
    {"route_type": 0, "route_type_name": "Train", "emoji": "🚂"},
    {"route_type": 1, "route_type_name": "Tram", "emoji": "🚃"},
    {"route_type": 2, "route_type_name": "Bus", "emoji": "🚌"},
    {"route_type": 3, "route_type_name": "VLine", "emoji": "🚆"},
    {"route_type": 4, "route_type_name": "Night Bus", "emoji": "🌙"},
]

def get_route_type_table():
    """Generate route type selection table"""
    msg = "📋 Select Route Type:\n\n"
    msg += "Reply with a number (0-4) or type 'all':\n\n"
    for rt in ROUTE_TYPES:
        msg += f"{rt['route_type']} - {rt['emoji']} {rt['route_type_name']}\n"
    msg += "all - Show all transport types\n"
    return msg

# PTV API Helper
def get_ptv_data(endpoint):
    """Fetch data from PTV API with HMAC signature"""
    timestamp = str(int(time.time()))
    # URL-encode the endpoint to handle spaces and special characters
    encoded_endpoint = urllib.parse.quote(endpoint, safe='/')
    path = f'/v3/{encoded_endpoint}'
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
        "/search <stop name> - Find a stop"
    )

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start search - ask for search term"""
    # Get search term from command arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /search <stop name>\n"
            "Example: /search Flinders Street\n"
            "Example: /search Box Hill"
        )
        return ConversationHandler.END
    
    # Store search term in user data
    search_term = ' '.join(context.args)
    context.user_data['search_term'] = search_term
    logger.info(f"User searching for: {search_term}")
    
    # Ask for route type selection
    await update.message.reply_text(
        f"🔍 Searching for: *{search_term}*\n\n"
        f"{get_route_type_table()}",
        parse_mode='Markdown'
    )
    
    return ASKING_ROUTE_TYPE

async def handle_route_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's route type selection"""
    user_input = update.message.text.strip().lower()
    search_term = context.user_data.get('search_term', '')
    
    # Validate input
    if user_input == 'all':
        route_type_filter = None
    elif user_input.isdigit() and int(user_input) in range(5):
        route_type_filter = int(user_input)
    else:
        await update.message.reply_text(
            "❌ Invalid input. Please enter a number from 0-4, or type 'all'.\n\n"
            + get_route_type_table(),
            parse_mode='Markdown'
        )
        return ASKING_ROUTE_TYPE
    
    # Fetch search results
    await update.message.reply_text(f"🔍 Fetching results for *{search_term}*...", parse_mode='Markdown')
    
    data = get_ptv_data(f'search/{search_term}')
    
    if not data or 'stops' not in data or not data['stops']:
        await update.message.reply_text(
            f"❌ No stops found for '{search_term}'.\n"
            "Try:\n"
            "- Check spelling\n"
            "- Use a simpler name (e.g., 'Flinders' instead of 'Flinders Street Railway Station')\n"
            "- Try a nearby major station"
        )
        return ConversationHandler.END
    
    # Filter stops by route type if specified
    stops = data['stops']
    if route_type_filter is not None:
        stops = [s for s in stops if s.get('route_type') == route_type_filter]
        type_name = ROUTE_TYPES[route_type_filter]['route_type_name']
        type_emoji = ROUTE_TYPES[route_type_filter]['emoji']
        header_msg = f"{type_emoji} *{type_name} stops* for '{search_term}':\n"
    else:
        header_msg = f"🔍 *All stops* for '{search_term}':\n"
    
    if not stops:
        await update.message.reply_text(
            f"❌ No {ROUTE_TYPES[route_type_filter]['route_type_name'].lower() if route_type_filter is not None else ''} stops found for '{search_term}'.\n"
            "Try searching with a different route type or 'all'."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(header_msg, parse_mode='Markdown')
    
    # Display stops (limited to 5)
    for i, stop in enumerate(stops[:5], 1):
        msg = format_stop_message(stop, i)
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    if len(stops) > 5:
        await update.message.reply_text(f"_...and {len(stops) - 5} more stop(s)_", parse_mode='Markdown')
    
    return ConversationHandler.END

def format_stop_message(stop, index=None):
    """Format stop results showing comprehensive route and stop information"""
    stop_name = stop.get('stop_name') or 'N/A'
    stop_id = stop.get('stop_id') or 'N/A'
    stop_suburb = stop.get('stop_suburb') or 'N/A'
    stop_landmark = stop.get('stop_landmark') or 'N/A'
    stop_latitude = stop.get('stop_latitude') or 'N/A'
    stop_longitude = stop.get('stop_longitude') or 'N/A'
    route_type = stop.get('route_type', 0)
    routes = stop.get('routes', [])
    
    # Get emoji and type name for route type
    rt_info = ROUTE_TYPES[route_type] if route_type < len(ROUTE_TYPES) else {"emoji": "❓", "route_type_name": "N/A"}
    emoji = rt_info['emoji']
    type_name = rt_info['route_type_name']
    
    # Build message
    msg = ""
    if index:
        msg += f"{index}. "
    msg += f"{emoji} {stop_name}\n"
    msg += f"   Transport Type: {type_name}\n"
    msg += f"   Suburb: {stop_suburb}\n"
    msg += f"   Stop ID: {stop_id}\n"
    msg += f"   Landmark: {stop_landmark}\n"
    msg += f"   Coordinates: {stop_latitude}, {stop_longitude}\n\n"
    
    # Add route information in comprehensive format
    if routes:
        for i, route in enumerate(routes[:3], 1):  # Limit to 3 routes per stop
            route_name = route.get('route_name') or 'N/A'
            route_number = route.get('route_number') or 'N/A'
            route_id = route.get('route_id') or 'N/A'
            route_gtfs_id = route.get('route_gtfs_id') or 'N/A'
            route_type_route = route.get('route_type')
            route_type_name = ROUTE_TYPES[route_type_route]['route_type_name'] if route_type_route and route_type_route < len(ROUTE_TYPES) else 'N/A'
            status_info = route.get('route_service_status') or {}
            status = status_info.get('description') or 'N/A'
            timestamp_str = status_info.get('timestamp') or ''
            
            # Parse and format timestamp with daylight savings (Melbourne time)
            formatted_time = 'N/A'
            if timestamp_str:
                try:
                    ts_clean = timestamp_str.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(ts_clean)
                    melbourne_tz = ZoneInfo('Australia/Melbourne')
                    dt_local = dt.astimezone(melbourne_tz)
                    formatted_time = dt_local.strftime("%H:%M:%S %d/%m/%Y")
                except:
                    formatted_time = 'N/A'
            
            msg += f"   Route {i}:\n"
            msg += f"      Route Name: {route_name}\n"
            msg += f"      Route Number: {route_number}\n"
            msg += f"      Route ID: {route_id}\n"
            msg += f"      GTFS ID: {route_gtfs_id}\n"
            msg += f"      Transport Type: {route_type_name}\n"
            msg += f"      Status: {status}\n"
            msg += f"      Timestamp: {formatted_time}\n\n"
        
        if len(routes) > 3:
            msg += f"   ...and {len(routes) - 3} more route(s)\n\n"
    else:
        msg += "   No routes available for this stop\n\n"
    
    msg += "---"
    return msg

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# Main function
def main():
    # Build application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    
    # Search conversation handler
    search_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_start)],
        states={
            ASKING_ROUTE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_route_type),
            ],
        },
        fallbacks=[],
    )
    application.add_handler(search_conv_handler)
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Run the bot (polling mode - no webhook needed)
    logger.info("Starting bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
