# AI Activity Logs

Format: `[YYYY-MM-DD HH:MM] - Description of work done`

---

## 2026-03-30 10:05
- Reviewed all 7 files in AI/ folder for improvement suggestions
- Fixed AI/README.md: Expanded from 7 lines to 40 lines with navigation table, project context, and constraints
- Fixed AI/DOCS.md: Corrected project structure diagram paths (AI files now shown in proper subdirectory)
- Fixed AI/AI.md: Clarified reading order to start with AI/README.md first
- Added Logging Requirements section to AI/AI.md
- Created AI/DEBUG.md with debugging steps for GitHub Pages, Telegram bot, PTV API, and frontend issues

## 2026-03-31 09:33
- **MAJOR ARCHITECTURE CHANGE**: Switched from "Web + Bot" to "Telegram Bot Only"
- Updated HOSTING.md: Removed Cloudflare tunnel setup, replaced with Telegram bot polling mode guide
- Updated AI/DOCS.md: Reflected bot-only architecture (removed website references)
- Updated AI/README.md: Updated project context and constraints for bot-only setup
- Simplified deployment: No domain, no Cloudflare, no port forwarding needed
- Raspberry Pi hosting via polling mode (outbound HTTPS only)

