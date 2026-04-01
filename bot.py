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
    msg = "📋 *Select Route Type:*\n\n"
    msg += "Please reply with the number (0-4) of your preferred transport mode:\n\n"
    msg += "```\n"
    msg += "┌─────┬─────────────┬────────┐\n"
    msg += "│ Num │ Type        │ Emoji  │\n"
    msg += "├─────┼─────────────┼────────┤\n"
    for rt in ROUTE_TYPES:
        msg += f"│  {rt['route_type']}  │ {rt['route_type_name']:<11} │ {rt['emoji']}   │\n"
    msg += "└─────┴─────────────┴────────┘\n"
    msg += "```\n\n"
    msg += "Or type 'all' to see stops for all route types."
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
        "/search <stop name> - Find a stop ID\n"
        "/help - Show all commands"
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
    """Format a single stop for display"""
    stop_name = stop.get('stop_name', 'Unknown')
    stop_id = stop.get('stop_id', 'Unknown')
    stop_suburb = stop.get('stop_suburb', '')
    route_type = stop.get('route_type', 0)
    routes = stop.get('routes', [])
    
    # Get emoji for route type
    rt_info = ROUTE_TYPES[route_type] if route_type < len(ROUTE_TYPES) else {"emoji": "❓", "route_type_name": "Unknown"}
    emoji = rt_info['emoji']
    mode_name = rt_info['route_type_name']
    
    # Build message
    msg = ""
    if index:
        msg += f"*{index}.* "
    msg += f"{emoji} *{stop_name}*\n"
    msg += f"📍 {stop_suburb} | Stop ID: `{stop_id}`\n"
    msg += f"🚏 {mode_name} Stop\n"
    
    # Add routes information
    if routes:
        msg += "\n🚌 *Routes:*\n"
        for route in routes[:3]:  # Limit to 3 routes per stop
            route_num = route.get('route_number', '??')
            route_name = route.get('route_name', 'Unknown')
            status = route.get('route_service_status', {}).get('description', 'Unknown')
            
            # Status emoji
            status_emoji = '✅' if 'Good' in status else '⚠️' if 'Suspended' not in status else '❌'
            
            # Shorten long route names
            if len(route_name) > 40:
                route_name = route_name[:37] + "..."
            
            msg += f"  • Route {route_num}: {route_name}\n"
            msg += f"    {status_emoji} {status}\n"
        
        if len(routes) > 3:
            msg += f"  _...and {len(routes) - 3} more route(s)_\n"
    
    msg += "\n`─────────────────────`"
    return msg

async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the search conversation"""
    await update.message.reply_text("❌ Search cancelled. Type /search to try again.")
    return ConversationHandler.END

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
    application.add_handler(CommandHandler("help", help_command))
    
    # Search conversation handler
    search_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_start)],
        states={
            ASKING_ROUTE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_route_type),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_search)],
    )
    application.add_handler(search_conv_handler)
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Run the bot (polling mode - no webhook needed)
    logger.info("Starting bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
