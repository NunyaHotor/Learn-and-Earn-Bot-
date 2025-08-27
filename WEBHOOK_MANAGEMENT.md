# Webhook Management Guide

This document explains how to manage webhook URLs for the LearnEarnAfrica Telegram bot.

## Webhook Configuration

The application uses the `WEBHOOK_URL` environment variable to configure webhook endpoints for:

1. **Telegram Bot**: `{WEBHOOK_URL}/webhook`
2. **NOWPayments**: `{WEBHOOK_URL}/webhook/nowpayments`

## Using the Webhook Manager Utility

A Python utility script `webhook_manager.py` has been created to easily manage webhook URLs.

### Installation

No additional installation is needed. The utility uses standard Python libraries.

### Basic Usage

```bash
# Show current webhook configuration
python webhook_manager.py --show

# Set new webhook URL
python webhook_manager.py --set https://b21b85927774.ngrok-free.app

# Test if webhook URL is accessible
python webhook_manager.py --test

# Use a different .env file
python webhook_manager.py --env-file .env.production --show
```

### Examples

**Update to ngrok URL:**
```bash
python webhook_manager.py --set https://b21b85927774.ngrok-free.app
```

**Update to production URL:**
```bash
python webhook_manager.py --set https://yourapp.com
```

**Check current configuration:**
```bash
python webhook_manager.py --show
```

### Manual Configuration

If you prefer to set the environment variable manually:

**Linux/macOS:**
```bash
export WEBHOOK_URL="https://b21b85927774.ngrok-free.app"
```

**Windows (Command Prompt):**
```cmd
set WEBHOOK_URL=https://b21b85927774.ngrok-free.app
```

**Windows (PowerShell):**
```powershell
$env:WEBHOOK_URL="https://b21b85927774.ngrok-free.app"
```

### Verifying Webhook Setup

After setting the webhook URL, you can verify it works by:

1. **Testing the URL:**
   ```bash
   python webhook_manager.py --test
   ```

2. **Checking the environment:**
   ```bash
   python webhook_manager.py --show
   ```

3. **Running the application:**
   ```bash
   python main.py
   ```

## Common Webhook Services

### ngrok (Development/Testing)
```bash
# Install ngrok
brew install ngrok/ngrok/ngrok  # macOS
# or download from https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8080

# Use the provided ngrok URL
python webhook_manager.py --set https://your-ngrok-url.ngrok.io
```

### Production Deployment
For production, use your actual domain:
```bash
python webhook_manager.py --set https://yourapp.com
```

## Troubleshooting

### Webhook URL not accessible
- Make sure your server is running and accessible
- Check firewall settings
- Verify the URL is correct

### Environment variables not loading
- Ensure the `.env` file exists in the project root
- Check file permissions
- Restart your terminal/IDE after changes

### Payment webhooks not working
- Verify NOWPayments is configured with the correct callback URL
- Check that the `/webhook/nowpayments` endpoint is properly set up

## Security Notes

- Always use HTTPS for production webhooks
- Keep your `.env` file secure and don't commit it to version control
- Regularly rotate ngrok URLs for development
- Monitor webhook endpoints for suspicious activity

## Support

For issues with webhook configuration, check:
- Application logs for webhook errors
- Telegram Bot API documentation
- NOWPayments webhook documentation
- ngrok documentation for tunnel issues
