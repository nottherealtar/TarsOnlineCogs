# Lesson Planner AI Cog

A RedBot cog that generates university lesson plans as PDFs via n8n workflow integration.

## Features

- Generate AI-powered lesson plans through n8n webhooks
- Rate limiting to prevent abuse (2 uses per minute per user)
- Secure configuration system for webhook URLs
- Connection testing capabilities
- Error handling and logging

## Installation

1. Add this cog to your RedBot cogs directory
2. Load the cog: `[p]load lessonplanner`
3. Configure the webhook URL (see Configuration section)

## Configuration

**⚠️ Important Security Notice**: This cog requires configuration of a webhook URL. Never commit sensitive URLs or API keys to public repositories.

### Setting up the webhook URL

1. **Bot Owner Only**: Use the configuration command to set your n8n webhook URL:
   ```
   [p]lessonplanset url http://your-n8n-instance.com/webhook/lesson-plan-pdf
   ```

2. **Test the connection**:
   ```
   [p]lessonplanset test
   ```

3. **View current configuration** (URL will be masked for security):
   ```
   [p]lessonplanset url
   ```

## Security Best Practices

### For Bot Owners
- Never share your webhook URLs publicly
- Use HTTPS URLs when possible
- Consider using environment variables or secure config files for sensitive data
- Regularly rotate API keys and webhook URLs
- Monitor usage logs for suspicious activity

### For Developers
- This cog stores configuration in RedBot's encrypted config system
- No sensitive data is hardcoded in the source code
- URLs are masked when displayed to users
- Only bot owners can configure webhook URLs

## Usage

Once configured, users can generate lesson plans:

```
[p]plan Learn Python programming in 3 months
[p]plan Advanced machine learning concepts over 6 weeks
```

## Commands

### User Commands
- `[p]plan <topic> <duration>` - Generate a lesson plan

### Owner Commands
- `[p]lessonplanset url [url]` - Set or view webhook URL
- `[p]lessonplanset test` - Test webhook connection

## Requirements

- RedBot 3.5.0+
- aiohttp (for HTTP requests)
- A configured n8n workflow with webhook endpoint

## Support

For issues or questions, please open an issue in the repository.

## License

This cog is provided as-is under the same license as the repository.
