# lpconnect

## Installation Guide

1. Install the required dependencies:
```bash
   pip install -r ./requirements.in
```

2. Create a .env file inside the bot directory.

3. Define the following variables inside the .env file:
```ini
   DISCORD_TOKEN=<your_discord_token>
   SOLANA_RPC=<your_solana_rpc_url>
   NOTIFICATION_CHANNEL_ID=<your_channel_id>
   COMMAND_PREFIX=lpconnect:
```
You can set the COMMAND_PREFIX to any value you prefer.

4. Run the bot:
```bash
   python ./bot/main.py
```

5. Check the bot connection by running the following command in the registered Discord notification channel:
```bash
   lpconnect:help
```