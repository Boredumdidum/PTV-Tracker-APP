# PTV Tracker Bot - Features

## Search Command

### `/search <stop name>`
Search for public transport stops by name.

**Example:** `/search Flinders Street`

**Flow:**
1. Enter stop name with command
2. Select transport type (Train, Tram, Bus, VLine, Night Bus, or All)
3. View summary table of matching stops
4. Select stops by number(s) to view detailed information

### Multi-Select Support
Enter one or more stop numbers to view details:
- Single: `3`
- Multiple: `1,5,7` or `2 4 6`
- Mixed: `1, 3 5`

### Paginated Results
Type `more` to load additional results in batches of 10:
- Initial view shows stops 1-10
- Each `more` shows next 10 results
- Progress indicator shows "X-Y of Z"
- When all results shown: "That's all results!"

## Transport Types

| Code | Type | Emoji |
|------|------|-------|
| 0 | Train | 🚂 |
| 1 | Tram | 🚃 |
| 2 | Bus | 🚌 |
| 3 | VLine | 🚆 |
| 4 | Night Bus | 🌙 |

Select by number or type `all` for all transport types.

## Stop Information Display

When you select stops, the bot shows:
- **Basic Info:** Name, Suburb, Stop ID, Landmark, Coordinates
- **Transport Type:** With emoji indicator
- **Routes:** Up to 3 routes per stop with:
  - Route name and number
  - Route ID and GTFS ID
  - Service status
  - Last updated timestamp (Melbourne time with daylight savings)

## Error Handling

- Invalid stop names: Suggests spelling corrections and simpler names
- Out-of-range numbers: Warns and asks for valid range
- Invalid input: Shows examples of correct formats
- Session expiry: Prompts to start new search

## Technical Features

- **HMAC Authentication:** Secure PTV API calls with signed requests
- **Rate Limiting Respected:** Follows PTV API guidelines
- **Timezone Aware:** Melbourne time with automatic daylight savings
- **Polling Mode:** Runs on Raspberry Pi without webhooks
- **Environment Security:** API keys stored securely via environment variables

---

## Future Roadmap

### Planned Commands
- [ ] `/help` - Show all available commands and usage examples
- [ ] `/track <stop_id>` - Add a stop to track for departures
- [ ] `/departures <stop_id>` - Get live departure information for a stop
- [ ] `/status` - Check status of tracked stops
- [ ] `/stop <stop_id>` - Stop tracking a specific stop
- [ ] `/list` - Show all tracked stops
- [ ] `/alerts` - Configure disruption notifications
- [ ] `/settings` - Manage user preferences

### Planned Features
- [ ] Real-time departure tracking with auto-refresh
- [ ] Push notifications for service disruptions
- [ ] Favorite stops saved per user
- [ ] Recent search history
- [ ] Inline keyboard buttons for common actions
- [ ] Estimated arrival times with live updates
- [ ] Route planning between two stops
- [ ] Group chat support for shared tracking

### Technical Improvements
- [ ] Caching layer for API responses (Redis)
- [ ] Database for user data and tracking lists
- [ ] Rate limiting and usage statistics
- [ ] Health check endpoint
- [ ] Logging and monitoring dashboard
