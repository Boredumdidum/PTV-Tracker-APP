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
ASKING_STOP_SELECTION = 2
VIEWING_STOP_DETAILS = 3
GUIDE_ASKING_ORIGIN = 4
GUIDE_ASKING_DESTINATION = 5
GUIDE_CONFIRM_ROUTE_TYPE = 6

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
        "/search <stop name> - Find a stop\n"
        "/guide <from> to <to> - Get route guidance"
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
    
    # Show stop summary table and ask for selection
    if not stops:
        await update.message.reply_text(
            f"❌ No {ROUTE_TYPES[route_type_filter]['route_type_name'].lower() if route_type_filter is not None else ''} stops found for '{search_term}'.\n"
            "Try searching with a different route type or 'all'."
        )
        return ConversationHandler.END
    
    # Store stops in user data for selection and track shown count
    context.user_data['found_stops'] = stops
    context.user_data['results_shown'] = 10
    
    # Display summary table
    msg = f"{header_msg}\n"
    msg += "Enter one or more numbers to view details (e.g., '1' or '1,2,3'), or type 'more' for more results:\n\n"
    
    for i, stop in enumerate(stops[:10], 1):
        stop_name = stop.get('stop_name', 'N/A')
        stop_suburb = stop.get('stop_suburb', 'N/A')
        route_type = stop.get('route_type', 0)
        rt_info = ROUTE_TYPES[route_type] if route_type < len(ROUTE_TYPES) else {"emoji": "❓"}
        emoji = rt_info['emoji']
        msg += f"{i}. {emoji} {stop_name} ({stop_suburb})\n"
    
    remaining = len(stops) - 10
    if remaining > 0:
        msg += f"\n...and {remaining} more stop(s). Type 'more' to see them."
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    
    return ASKING_STOP_SELECTION

def format_stop_message(stop, index=None, routes_shown=3, routes_start=0):
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
        end_idx = min(routes_start + routes_shown, len(routes))
        for i, route in enumerate(routes[routes_start:end_idx], routes_start + 1):
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
        
        remaining_routes = len(routes) - end_idx
        if remaining_routes > 0:
            msg += f"   ...and {remaining_routes} more route(s)\n\n"
    else:
        msg += "   No routes available for this stop\n\n"
    
    msg += "---"
    return msg

async def handle_stop_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's stop selection from the table or 'more' request"""
    user_input = update.message.text.strip().lower()
    stops = context.user_data.get('found_stops', [])
    results_shown = context.user_data.get('results_shown', 10)
    
    if not stops:
        await update.message.reply_text("❌ Session expired. Please start a new search with /search")
        return ConversationHandler.END
    
    # Handle 'more' request
    if user_input == 'more':
        remaining = len(stops) - results_shown
        if remaining <= 0:
            await update.message.reply_text("ℹ️ No more results available.")
            return ASKING_STOP_SELECTION
        
        # Show next 10 results
        start_idx = results_shown
        end_idx = min(start_idx + 10, len(stops))
        
        msg = f"📋 More results ({start_idx + 1}-{end_idx} of {len(stops)}):\n\n"
        for i, stop in enumerate(stops[start_idx:end_idx], start_idx + 1):
            stop_name = stop.get('stop_name', 'N/A')
            stop_suburb = stop.get('stop_suburb', 'N/A')
            route_type = stop.get('route_type', 0)
            rt_info = ROUTE_TYPES[route_type] if route_type < len(ROUTE_TYPES) else {"emoji": "❓"}
            emoji = rt_info['emoji']
            msg += f"{i}. {emoji} {stop_name} ({stop_suburb})\n"
        
        # Update shown count
        context.user_data['results_shown'] = end_idx
        
        remaining_after = len(stops) - end_idx
        if remaining_after > 0:
            msg += f"\n...and {remaining_after} more stop(s). Type 'more' to continue."
        else:
            msg += "\n\nThat's all results! Enter numbers to view details."
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return ASKING_STOP_SELECTION
    
    # Parse numbers from input (comma, space, or mixed separated)
    import re
    numbers = re.findall(r'\d+', user_input)
    
    if not numbers:
        await update.message.reply_text(
            "❌ Invalid input. Please enter one or more numbers, or type 'more'.\n"
            "Examples: '1', '2,3', '1 3 5', or 'more'"
        )
        return ASKING_STOP_SELECTION
    
    # Convert to integers and validate
    selected_indices = []
    for num_str in numbers:
        idx = int(num_str) - 1  # Convert to 0-based index
        if 0 <= idx < len(stops):
            selected_indices.append(idx)
        else:
            await update.message.reply_text(
                f"⚠️ Number {num_str} is out of range. Please enter numbers between 1 and {len(stops)}."
            )
            return ASKING_STOP_SELECTION
    
    # Remove duplicates while preserving order
    seen = set()
    unique_indices = []
    for idx in selected_indices:
        if idx not in seen:
            seen.add(idx)
            unique_indices.append(idx)
    
    # Show details for selected stops with initial route batch and prompt for more
    await update.message.reply_text(
        f"📍 Showing details for {len(unique_indices)} stop(s):\n"
    )
    
    for i, idx in enumerate(unique_indices, 1):
        stop = stops[idx]
        msg = format_stop_message(stop, idx + 1, routes_shown=3)
        await update.message.reply_text(msg, parse_mode='Markdown')
        
        # Store stop data for potential 'more' requests
        total_routes = len(stop.get('routes', []))
        if total_routes > 3:
            context.user_data['current_stop'] = stop
            context.user_data['current_stop_index'] = idx + 1
            context.user_data['routes_shown'] = 3
            await update.message.reply_text(
                "Type 'more' to see additional routes for this stop, or enter another stop number."
            )
            return VIEWING_STOP_DETAILS
    
    return ConversationHandler.END

async def handle_route_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'more' request for additional routes or new stop selection"""
    user_input = update.message.text.strip().lower()
    stops = context.user_data.get('found_stops', [])
    current_stop = context.user_data.get('current_stop')
    
    if not current_stop:
        await update.message.reply_text("❌ Session expired. Please start a new search with /search")
        return ConversationHandler.END
    
    # Handle 'more' request for routes
    if user_input == 'more':
        routes = current_stop.get('routes', [])
        routes_shown = context.user_data.get('routes_shown', 3)
        stop_index = context.user_data.get('current_stop_index', 1)
        
        remaining = len(routes) - routes_shown
        if remaining <= 0:
            await update.message.reply_text("ℹ️ No more routes available for this stop.")
            return VIEWING_STOP_DETAILS
        
        # Show next 3 routes
        start_idx = routes_shown
        end_idx = min(start_idx + 3, len(routes))
        
        msg = f"📍 {current_stop.get('stop_name')} - More Routes ({start_idx + 1}-{end_idx} of {len(routes)}):\n\n"
        
        for i, route in enumerate(routes[start_idx:end_idx], start_idx + 1):
            route_name = route.get('route_name') or 'N/A'
            route_number = route.get('route_number') or 'N/A'
            route_id = route.get('route_id') or 'N/A'
            route_gtfs_id = route.get('route_gtfs_id') or 'N/A'
            route_type_route = route.get('route_type')
            route_type_name = ROUTE_TYPES[route_type_route]['route_type_name'] if route_type_route and route_type_route < len(ROUTE_TYPES) else 'N/A'
            status_info = route.get('route_service_status') or {}
            status = status_info.get('description') or 'N/A'
            timestamp_str = status_info.get('timestamp') or ''
            
            # Parse and format timestamp
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
        
        # Update shown count
        context.user_data['routes_shown'] = end_idx
        
        remaining_after = len(routes) - end_idx
        if remaining_after > 0:
            msg += f"...and {remaining_after} more route(s). Type 'more' to continue."
        else:
            msg += "That's all routes for this stop!"
        
        msg += "\n\nEnter another stop number or type 'done' to finish."
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return VIEWING_STOP_DETAILS
    
    # Handle 'done' to end conversation
    if user_input == 'done':
        await update.message.reply_text("Search complete! Use /search to find more stops.")
        return ConversationHandler.END
    
    # Handle new stop selection
    import re
    numbers = re.findall(r'\d+', user_input)
    
    if numbers:
        # User selected a different stop, process it
        selected_idx = int(numbers[0]) - 1
        if 0 <= selected_idx < len(stops):
            stop = stops[selected_idx]
            msg = format_stop_message(stop, selected_idx + 1, routes_shown=3)
            await update.message.reply_text(msg, parse_mode='Markdown')
            
            total_routes = len(stop.get('routes', []))
            if total_routes > 3:
                context.user_data['current_stop'] = stop
                context.user_data['current_stop_index'] = selected_idx + 1
                context.user_data['routes_shown'] = 3
                await update.message.reply_text(
                    "Type 'more' to see additional routes, 'done' to finish, or another stop number."
                )
                return VIEWING_STOP_DETAILS
            else:
                await update.message.reply_text("Enter another stop number or type 'done' to finish.")
                return VIEWING_STOP_DETAILS
        else:
            await update.message.reply_text(
                f"⚠️ Invalid stop number. Please enter 1-{len(stops)}, 'more', or 'done'."
            )
            return VIEWING_STOP_DETAILS
    
    # Invalid input
    await update.message.reply_text(
        "❌ Invalid input. Type 'more' for more routes, a stop number, or 'done' to finish."
    )
    return VIEWING_STOP_DETAILS

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# Guide Command Handlers
async def guide_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start route guidance - parse origin and destination from args or ask interactively"""
    # Check if user provided origin/destination in command
    if context.args:
        full_input = ' '.join(context.args).lower()
        # Parse format: "origin to destination"
        if ' to ' in full_input:
            parts = full_input.split(' to ', 1)
            origin = parts[0].strip()
            destination = parts[1].strip()
            
            context.user_data['guide_origin'] = origin
            context.user_data['guide_destination'] = destination
            
            await update.message.reply_text(
                f"🗺️ Finding route from *{origin}* to *{destination}*...\n\n"
                f"{get_route_type_table()}",
                parse_mode='Markdown'
            )
            return GUIDE_CONFIRM_ROUTE_TYPE
    
    # Interactive mode - ask for origin
    await update.message.reply_text(
        "🗺️ Route Planner\n\n"
        "Where are you starting from?\n"
        "(e.g., 'Box Hill', 'Flinders Street', 'Glen Waverley')"
    )
    return GUIDE_ASKING_ORIGIN

async def guide_handle_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle origin input"""
    origin = update.message.text.strip()
    context.user_data['guide_origin'] = origin
    
    await update.message.reply_text(
        f"📍 Starting from: *{origin}*\n\n"
        f"Where do you want to go?",
        parse_mode='Markdown'
    )
    return GUIDE_ASKING_DESTINATION

async def guide_handle_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle destination input"""
    destination = update.message.text.strip()
    context.user_data['guide_destination'] = destination
    
    await update.message.reply_text(
        f"🗺️ Route: *{context.user_data['guide_origin']}* → *{destination}*\n\n"
        f"{get_route_type_table()}",
        parse_mode='Markdown'
    )
    return GUIDE_CONFIRM_ROUTE_TYPE

async def guide_handle_route_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transport type selection and find connecting routes"""
    user_input = update.message.text.strip().lower()
    origin = context.user_data.get('guide_origin', '')
    destination = context.user_data.get('guide_destination', '')
    
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
        return GUIDE_CONFIRM_ROUTE_TYPE
    
    await update.message.reply_text(
        f"🔍 Finding routes from *{origin}* to *{destination}*...",
        parse_mode='Markdown'
    )
    
    # Search for origin and destination stops
    origin_data = get_ptv_data(f'search/{urllib.parse.quote(origin)}')
    dest_data = get_ptv_data(f'search/{urllib.parse.quote(destination)}')
    
    if not origin_data or 'stops' not in origin_data or not origin_data['stops']:
        await update.message.reply_text(
            f"❌ No stops found for origin '{origin}'.\n"
            "Try a different name or check spelling."
        )
        return ConversationHandler.END
    
    if not dest_data or 'stops' not in dest_data or not dest_data['stops']:
        await update.message.reply_text(
            f"❌ No stops found for destination '{destination}'.\n"
            "Try a different name or check spelling."
        )
        return ConversationHandler.END
    
    # Filter by route type if specified
    origin_stops = origin_data['stops']
    dest_stops = dest_data['stops']
    
    if route_type_filter is not None:
        origin_stops = [s for s in origin_stops if s.get('route_type') == route_type_filter]
        dest_stops = [s for s in dest_stops if s.get('route_type') == route_type_filter]
    
    if not origin_stops:
        await update.message.reply_text(f"❌ No {ROUTE_TYPES[route_type_filter]['route_type_name'].lower()} stops found for '{origin}'.")
        return ConversationHandler.END
    
    if not dest_stops:
        await update.message.reply_text(f"❌ No {ROUTE_TYPES[route_type_filter]['route_type_name'].lower()} stops found for '{destination}'.")
        return ConversationHandler.END
    
    # Find connecting routes
    route_suggestions = find_connecting_routes(origin_stops, dest_stops, route_type_filter)
    
    if not route_suggestions:
        await update.message.reply_text(
            "❌ No direct routes found between these locations.\n\n"
            "Try:\n"
            "- Use 'all' transport types\n"
            "- Check different stop names\n"
            "- Consider nearby major stations"
        )
        return ConversationHandler.END
    
    # Display route suggestions
    type_name = ROUTE_TYPES[route_type_filter]['route_type_name'] if route_type_filter else 'All'
    type_emoji = ROUTE_TYPES[route_type_filter]['emoji'] if route_type_filter else '🗺️'
    
    msg = f"{type_emoji} *{type_name} routes from {origin} to {destination}:*\n\n"
    
    for i, suggestion in enumerate(route_suggestions[:5], 1):
        msg += format_route_suggestion(suggestion, i)
        msg += "\n"
    
    if len(route_suggestions) > 5:
        msg += f"_...and {len(route_suggestions) - 5} more options_\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    return ConversationHandler.END

def find_connecting_routes(origin_stops, dest_stops, route_type_filter=None):
    """Find routes that connect origin to destination"""
    suggestions = []
    
    # Build sets of route IDs for origin and destination stops
    origin_routes = {}  # route_id -> list of stops
    dest_routes = {}    # route_id -> list of stops
    
    for stop in origin_stops:
        for route in stop.get('routes', []):
            route_id = route.get('route_id')
            if route_id:
                if route_id not in origin_routes:
                    origin_routes[route_id] = {'route': route, 'stops': []}
                origin_routes[route_id]['stops'].append(stop)
    
    for stop in dest_stops:
        for route in stop.get('routes', []):
            route_id = route.get('route_id')
            if route_id:
                if route_id not in dest_routes:
                    dest_routes[route_id] = {'route': route, 'stops': []}
                dest_routes[route_id]['stops'].append(stop)
    
    # Find common routes
    common_route_ids = set(origin_routes.keys()) & set(dest_routes.keys())
    
    for route_id in common_route_ids:
        route_info = origin_routes[route_id]['route']
        origin_stop_names = [s.get('stop_name') for s in origin_routes[route_id]['stops']]
        dest_stop_names = [s.get('stop_name') for s in dest_routes[route_id]['stops']]
        
        suggestions.append({
            'route': route_info,
            'origin_stops': origin_stop_names[:2],  # Limit to 2
            'dest_stops': dest_stop_names[:2],
            'route_type': route_info.get('route_type', 0)
        })
    
    return suggestions

def format_route_suggestion(suggestion, index):
    """Format a route suggestion for display"""
    route = suggestion['route']
    route_name = route.get('route_name', 'N/A')
    route_number = route.get('route_number', '')
    route_type = suggestion['route_type']
    
    rt_info = ROUTE_TYPES[route_type] if route_type < len(ROUTE_TYPES) else {"emoji": "❓", "route_type_name": "Unknown"}
    emoji = rt_info['emoji']
    type_name = rt_info['route_type_name']
    
    display_name = f"{route_number} - {route_name}" if route_number else route_name
    
    msg = f"{index}. {emoji} *{display_name}* ({type_name})\n"
    msg += f"   🚏 Board at: {', '.join(suggestion['origin_stops'])}\n"
    msg += f"   🎯 Alight at: {', '.join(suggestion['dest_stops'])}\n"
    
    return msg

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
            ASKING_STOP_SELECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stop_selection),
            ],
            VIEWING_STOP_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_route_pagination),
            ],
        },
        fallbacks=[],
    )
    application.add_handler(search_conv_handler)
    
    # Guide conversation handler
    guide_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("guide", guide_start)],
        states={
            GUIDE_ASKING_ORIGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guide_handle_origin),
            ],
            GUIDE_ASKING_DESTINATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guide_handle_destination),
            ],
            GUIDE_CONFIRM_ROUTE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guide_handle_route_type),
            ],
        },
        fallbacks=[],
    )
    application.add_handler(guide_conv_handler)
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Run the bot (polling mode - no webhook needed)
    logger.info("Starting bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
