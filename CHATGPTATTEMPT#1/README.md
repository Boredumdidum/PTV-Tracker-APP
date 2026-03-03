# Public Transport Victoria (PTV) Tracker App

This app displays real-time public transport information (trains, trams, buses) for Victoria, Australia.

## Stack
- Frontend: React
- Backend: Node.js/Express
- API Integration: PTV API

## Structure
- `/client` - React frontend
- `/server` - Node.js/Express backend

## Features
- Map view of transport locations
- List of upcoming services
- Real-time updates (PTV API integration)

## Getting Started

### Prerequisites
- Node.js & npm installed

### Setup
1. Install dependencies for both frontend and backend:
   - `cd client && npm install`
   - `cd ../server && npm install`
2. Start backend:
   - `cd server && npm start`
3. Start frontend:
   - `cd client && npm start`

### API Keys
- You will need a PTV API key. See `/server/README.md` for setup.

---

## Development
- Frontend runs on [http://localhost:3000](http://localhost:3000)
- Backend runs on [http://localhost:5000](http://localhost:5000)

---

## License
MIT
