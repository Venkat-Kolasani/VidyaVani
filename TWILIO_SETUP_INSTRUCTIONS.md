# Twilio Setup Instructions for VidyaVani

## Quick Start

### 1. Get Your Twilio Credentials

1. **Sign up for Twilio**: https://www.twilio.com/try-twilio
2. **Get your credentials** from the Twilio Console Dashboard:
   - Account SID (starts with `AC...`)
   - Auth Token (click "Show" to reveal)
3. **Buy a US phone number**:
   - Go to Phone Numbers → Buy a Number
   - Filter by United States
   - Select a number with Voice capabilities
   - Complete purchase ($1/month)

### 2. Update Environment Variables

#### For Local Development
Edit your `.env` file:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
BASE_URL=http://localhost:5001
```

#### For Production (Render.com)
Add these in Render Dashboard → Environment:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
BASE_URL=https://vidyavani.onrender.com
```

### 3. Install Twilio SDK

```bash
pip install twilio
```

### 4. Run Setup Script

```bash
python scripts/setup_twilio.py
```

This will:
- ✅ Validate your credentials
- ✅ Test Twilio connection
- ✅ Show your account balance
- ✅ Display webhook URLs

### 5. Configure Twilio Webhooks

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/active
2. Click on your phone number
3. Scroll to "Voice Configuration"
4. Set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://vidyavani.onrender.com/webhook/incoming-call`
   - **HTTP Method**: POST
5. Click **Save**

### 6. Test Your Setup

Call your Twilio number and follow the IVR prompts!

## What Changed from Exotel?

### Files Created
- `src/ivr/twilio_client.py` - New Twilio client
- `docs/TWILIO_MIGRATION_GUIDE.md` - Detailed migration guide
- `scripts/setup_twilio.py` - Setup validation script

### Files Updated
- `config.py` - Added Twilio configuration
- `requirements.txt` - Added twilio package
- `.env` - Updated with Twilio credentials
- `RENDER_ENV_VARS.txt` - Updated for production

### Key Differences
1. **Authentication**: Uses Twilio SDK instead of basic auth
2. **Response Format**: TwiML (Python objects) instead of XML strings
3. **Phone Format**: E.164 format required (+15551234567)
4. **Webhooks**: Different parameter names (CallSid vs call_sid)

## Webhook URLs

Your VidyaVani instance will handle these webhooks:

| Endpoint | Purpose |
|----------|---------|
| `/webhook/incoming-call` | Initial call handling |
| `/webhook/process-input` | DTMF input processing |
| `/webhook/process-recording` | Audio recording processing |
| `/webhook/sms` | SMS handling (optional) |

## Testing Locally with ngrok

If you want to test locally before deploying:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from ngrok.com

# Start your app
python app.py

# In another terminal
ngrok http 5001

# Use the ngrok URL in Twilio webhook config
# Example: https://abc123.ngrok.io/webhook/incoming-call
```

## Monitoring

### Twilio Console
- **Call Logs**: https://console.twilio.com/us1/monitor/logs/calls
- **Debugger**: https://console.twilio.com/us1/monitor/debugger
- **Usage**: https://console.twilio.com/us1/monitor/usage

### Your Application
- Check Render logs for webhook requests
- Monitor `/api/health` endpoint
- Review performance dashboard

## Costs

- **Phone Number**: $1/month
- **Incoming Calls**: $0.0085/minute
- **Outgoing Calls**: $0.013/minute
- **SMS**: $0.0075/message

**Estimated for demo**: ~$5-10/month for light usage

## Troubleshooting

### "Webhook not receiving calls"
- ✅ Verify webhook URL is correct in Twilio Console
- ✅ Check Render logs for incoming requests
- ✅ Ensure app is deployed and running

### "Invalid credentials"
- ✅ Double-check Account SID and Auth Token
- ✅ Make sure no extra spaces in .env file
- ✅ Restart app after updating credentials

### "Audio not playing"
- ✅ Verify audio URL is publicly accessible
- ✅ Check audio format (WAV or MP3)
- ✅ Test URL in browser

### "Recording not working"
- ✅ Check RecordingUrl parameter in webhook
- ✅ Verify recording callback URL
- ✅ Check Twilio debugger for errors

## Support

- **Twilio Docs**: https://www.twilio.com/docs
- **Python SDK**: https://www.twilio.com/docs/libraries/python
- **Support**: https://support.twilio.com
- **Community**: https://www.twilio.com/community

## Next Steps

1. ✅ Complete setup steps above
2. ✅ Test by calling your Twilio number
3. ✅ Monitor first few calls in Twilio Console
4. ✅ Update presentation with new phone number
5. ✅ Document any issues for team

---

**Need Help?** Check `docs/TWILIO_MIGRATION_GUIDE.md` for detailed information.
