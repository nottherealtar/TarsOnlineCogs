# TVideo - AI Video Generation Cog

A RedBot cog that integrates with Pipedream to generate AI videos from text prompts.

## Features

- Simple `[p]request <prompt>` command to generate videos
- Integration with Pipedream webhook for AI video generation
- Real-time status updates showing request progress
- Optional API key configuration for authentication
- Admin controls for configuration

## Setup

1. Install the cog: `[p]load tvideo`
2. **REQUIRED**: Set your Pipedream webhook URL: `[p]tvideo setwebhook <your_webhook_url>`
3. (Optional) Set an API key: `[p]tvideo setkey <your_api_key>`
4. (Optional) Set notification channel: `[p]tvideo setchannel #channel`
5. Check status: `[p]tvideo status`

⚠️ **Security Note**: Keep your webhook URL private! Don't share it publicly as it could be abused.

## Usage

### Generate a Video
```
[p]request Create a short video of a cat playing with a ball
```

### Check Configuration
```
[p]tvideo status
```

### Admin Commands
```
[p]tvideo setwebhook <webhook_url> # Set Pipedream webhook URL (REQUIRED)
[p]tvideo setkey <api_key>         # Set API key (optional)
[p]tvideo setchannel #channel      # Set notification channel
[p]tvideo setup                    # Show setup help
```

## How It Works

1. User sends a video request with `[p]request <prompt>`
2. Cog sends the request to your configured Pipedream webhook
3. Pipedream processes the request and handles video generation
4. Response handling is managed by Pipedream flow (not the Discord bot)

## Request Data Format

The cog sends the following data to Pipedream:

```json
{
    "prompt": "user's video prompt",
    "user_id": "Discord user ID",
    "user_name": "Discord username",
    "guild_id": "Discord server ID", 
    "channel_id": "Discord channel ID",
    "message_id": "Discord message ID",
    "api_key": "optional API key"
}
```

## Requirements

- aiohttp (automatically installed)
- RedBot 3.5.0+
- Pipedream webhook endpoint configured
