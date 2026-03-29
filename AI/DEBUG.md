# Debugging Guide for PTV-Tracker-APP

## General Debugging Approach

1. **Identify the symptom** - What is failing?
2. **Check logs** - Look at browser console, server logs, bot logs
3. **Isolate the issue** - Reproduce consistently
4. **Apply fix** - Make minimal targeted change
5. **Verify** - Test the fix thoroughly
6. **Document** - Update LOGS.md with findings

---

## GitHub Pages Issues

### Site Not Loading
- Check repository settings → Pages → Source branch
- Verify `index.html` exists in root or docs folder
- Confirm no 404 errors in browser console

### Assets Not Loading (CSS/JS)
- Check file paths are relative (`./style.css` not `/style.css`)
- Verify files are committed to the correct branch
- Check case sensitivity in file names

### Build Failures
- Review `.github/workflows` logs
- Check for Jekyll build errors
- Verify no syntax errors in YAML files

---

## Telegram Bot Issues

### Bot Not Responding
- Verify bot token is valid and not expired
- Check webhook URL is accessible from internet
- Confirm HTTPS is enabled on webhook endpoint
- Test with polling mode first, then switch to webhook

### Webhook Problems
```bash
# Check current webhook
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Delete webhook (fallback to polling)
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

### Message Parsing Errors
- Validate JSON payload structure
- Check for UTF-8 encoding issues
- Verify message length limits (4096 chars max)

---

## PTV API Issues

### API Connection Failures
- Verify API key is active and not rate-limited
- Check network connectivity
- Confirm correct base URL: `https://timetableapi.ptv.vic.gov.au`

### Rate Limiting (429 Errors)
- Implement exponential backoff
- Cache responses appropriately
- Check `X-RateLimit-Remaining` headers

### Authentication Errors
- Verify DevID and API key combination
- Check signature generation for HMAC
- Ensure timestamp is current

---

## Frontend Issues

### JavaScript Errors
- Check browser console for errors
- Verify all dependencies loaded (network tab)
- Test in incognito mode (no extensions)

### Styling Problems
- Confirm CSS specificity hierarchy
- Check for conflicting styles
- Test responsive breakpoints

### API Calls Failing
- Check CORS headers if calling external APIs
- Verify fetch/axios error handling
- Inspect request/response in Network tab

---

## Common Error Patterns

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| 404 on assets | Wrong path or file missing | Check relative paths |
| Bot 401 | Invalid token | Regenerate via @BotFather |
| PTV 403 | Auth failure | Regenerate DevID/Key |
| CORS error | Missing headers | Add CORS middleware |
| Module not found | Missing dependency | Run `npm install` |

---

## Testing Checklist

Before marking bug as fixed:
- [ ] Bug is reproducible before fix
- [ ] Fix resolves the specific issue
- [ ] No regressions introduced
- [ ] Tested in production-like environment
- [ ] Logs updated with root cause

---

## Emergency Fallbacks

If critical failure:
1. Revert to last known working commit
2. Enable verbose logging everywhere
3. Deploy minimal reproduction case
4. Document findings in LOGS.md
