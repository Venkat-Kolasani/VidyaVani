# Exotel Setup Guide for VidyaVani IVR System

This guide will help you set up Exotel for the VidyaVani AI-powered IVR learning system.

## Why Exotel?

Exotel is a leading cloud telephony platform in India that provides:
- Better connectivity for Indian phone numbers
- Cost-effective calling rates within India
- Robust IVR capabilities
- Easy integration with REST APIs
- Support for both incoming and outgoing calls

## Getting Started with Exotel

### 1. Create an Exotel Account

1. Visit [Exotel Console](https://my.exotel.com/signup)
2. Sign up for a new account
3. Complete the verification process
4. Choose a suitable plan (they offer free trial credits)

### 2. Get Your API Credentials

After logging into your Exotel dashboard:

1. **Account SID**: Found in your dashboard under "Account Details"
2. **API Key**: Go to Settings → API Settings → Generate API Key
3. **API Token**: Generated along with the API Key
4. **Phone Number**: Purchase a phone number from Exotel dashboard
5. **App ID**: Create an app in the Apps section for IVR flow

### 3. Configure Your Exotel App

1. Go to "Apps" in your Exotel dashboard
2. Create a new app with the following settings:
   - **App Type**: Connect (for IVR)
   - **Answer URL**: `https://your-domain.com/webhook/incoming-call`
   - **Hangup URL**: `https://your-domain.com/webhook/hangup`
   - **Passthru URL**: `https://your-domain.com/webhook/passthru`

### 4. Environment Variables

Add these to your `.env` file:

```bash
# Exotel Configuration
EXOTEL_ACCOUNT_SID=your_account_sid_here
EXOTEL_API_KEY=your_api_key_here
EXOTEL_API_TOKEN=your_api_token_here
EXOTEL_PHONE_NUMBER=your_exotel_phone_number
EXOTEL_APP_ID=your_app_id_here
```

## Exotel API Endpoints

The VidyaVani system will use these Exotel API endpoints:

### 1. Make Outbound Calls
```
POST https://api.exotel.com/v1/Accounts/{AccountSid}/Calls/connect.json
```

### 2. Send SMS
```
POST https://api.exotel.com/v1/Accounts/{AccountSid}/Sms/send.json
```

### 3. Get Call Details
```
GET https://api.exotel.com/v1/Accounts/{AccountSid}/Calls/{CallSid}.json
```

## Webhook Configuration

Your VidyaVani application will receive webhooks from Exotel at these endpoints:

- **Incoming Call**: `/webhook/incoming-call`
- **Call Status**: `/webhook/call-status`
- **Passthru**: `/webhook/passthru`

## Testing Your Setup

1. **Test API Connection**:
   ```bash
   curl -X GET "https://api.exotel.com/v1/Accounts/{AccountSid}/Calls.json" \
        -u "{APIKey}:{APIToken}"
   ```

2. **Test Phone Number**:
   - Call your Exotel number
   - Check if webhooks are received in your application logs

## Pricing

Exotel pricing for India (approximate):
- **Incoming calls**: ₹0.30-0.50 per minute
- **Outgoing calls**: ₹0.40-0.80 per minute
- **SMS**: ₹0.15-0.25 per SMS
- **Phone number rental**: ₹500-1000 per month

## Support

- **Exotel Documentation**: https://developer.exotel.com/
- **Support**: support@exotel.com
- **Developer Forum**: https://community.exotel.com/

## Security Best Practices

1. **Keep credentials secure**: Never commit API keys to version control
2. **Use HTTPS**: Always use HTTPS for webhook URLs
3. **Validate webhooks**: Verify incoming webhook signatures
4. **Rate limiting**: Implement rate limiting for API calls
5. **Monitor usage**: Keep track of API usage and costs

## Troubleshooting

### Common Issues:

1. **Webhook not received**:
   - Check if your server is publicly accessible
   - Verify webhook URL in Exotel app configuration
   - Check firewall settings

2. **API authentication failed**:
   - Verify API Key and Token are correct
   - Check if credentials are properly base64 encoded

3. **Call quality issues**:
   - Check network connectivity
   - Verify audio codec settings
   - Test with different phone numbers

### Debug Mode:

Enable debug logging in your application to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

After setting up Exotel:

1. Test the basic webhook integration
2. Implement call flow logic
3. Add speech recognition and synthesis
4. Test end-to-end functionality
5. Monitor performance and costs