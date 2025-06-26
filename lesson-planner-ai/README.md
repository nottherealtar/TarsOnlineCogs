# Lesson Planner AI Cog

A RedBot cog that generates university lesson plans as PDFs via n8n workflow integration with full ngrok support.

## Features

- Generate AI-powered lesson plans through n8n webhooks
- **ngrok compatibility** with automatic header handling
- Easy ngrok URL updates when your tunnel changes
- Rate limiting to prevent abuse (2 uses per minute per user)
- Secure configuration system for webhook URLs
- Connection testing and debugging capabilities
- Error handling and comprehensive logging

## Quick Start

1. **Install the cog**: `[p]load lessonplanner`
2. **Update your ngrok domain**: `[p]lessonplanset ngrok YOUR_NGROK_DOMAIN`
3. **Test the connection**: `[p]lessonplanset test`
4. **Start generating plans**: `[p]plan Learn Python in 3 months`

## Configuration

### Setting up with ngrok (Recommended)

1. **Start ngrok** on your local machine:
   ```bash
   ngrok http 5678
   ```

2. **Update the domain** (easy command for ngrok users):
   ```
   [p]lessonplanset ngrok 0d09-102-135-142-207.ngrok-free.app
   ```
   This automatically adds the correct path and tests the connection!

3. **Verify it's working**:
   ```
   [p]lessonplanset test
   ```

### Manual URL Configuration

For other setups, use the manual URL command:
```
[p]lessonplanset url https://your-domain.com/lesson-plan-pdf
```

## Commands

### User Commands
- `[p]plan <topic> <duration>` - Generate a lesson plan

### Owner Commands
- `[p]lessonplanset ngrok <domain>` - Quick ngrok domain update
- `[p]lessonplanset url [url]` - Set or view webhook URL manually
- `[p]lessonplanset test` - Test webhook connection
- `[p]lessonplanset debug <url>` - Test a specific URL without saving

## Usage Examples

```
[p]plan Learn Python programming in 3 months
[p]plan Advanced machine learning concepts over 6 weeks
[p]plan Master digital marketing in 8 weeks
```

## ngrok Best Practices

### When ngrok restarts
Your ngrok URL changes every time you restart it. Simply run:
```
[p]lessonplanset ngrok NEW_DOMAIN_HERE
```

### Free vs Paid ngrok
- **Free**: URL changes on restart, limited connections
- **Paid**: Static domain, more reliable for production

## Security Features

- No sensitive data hardcoded in source
- URLs are masked when displayed
- Only bot owners can configure webhooks
- Automatic ngrok browser warning bypass
- Secure config storage in RedBot's encrypted system

## Requirements

- RedBot 3.5.0+
- aiohttp (for HTTP requests)
- A running n8n instance with webhook endpoint
- ngrok (recommended) or other tunnel solution

## Troubleshooting

### Common Issues
1. **"Connection refused"**: n8n isn't running or wrong port
2. **"Timeout"**: Network issue or firewall blocking
3. **"404 Not Found"**: Wrong webhook path in n8n
4. **"ngrok URL changed"**: Run `[p]lessonplanset ngrok NEW_DOMAIN`

### Debug Commands
```bash
# Test current configuration
[p]lessonplanset test

# Test a specific URL without saving
[p]lessonplanset debug https://test-domain.ngrok.io/lesson-plan-pdf

# View current settings (URL will be masked)
[p]lessonplanset url
```

## Support

For issues or questions, please open an issue in the repository.

## License

This cog is provided as-is under the same license as the repository.
