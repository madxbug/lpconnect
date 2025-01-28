# LPConnect - Meteora Discord Bots

## **Project Overview**
The **LPFeed** and **LPArena** bots are Python-based tools designed to revolutionize how liquidity providers (LPs)
interact, collaborate, and track their positions on Discord.
Built to enhance the experience of Meteora LP Army,
these bots provide real-time updates, automate tasks, and foster an engaging and educational community.

Whether you're an individual user or part of a DAO, these bots streamline wallet tracking, position sharing,
and community engagement to promote learning and collaboration.

## **Project Vision**
To create a vibrant and collaborative ecosystem where liquidity providers can track their activity, 
share insights, and grow together. By automating processes, providing privacy options, 
and enabling real-time analytics, **LPFeed** and **LPArena** aim to be essential tools for the LP Army community.


## Bots at a Glance

### 1. LPFeed Bot
Focused on simplifying tracking and automating discussions around liquidity provider activity.

**Key Features**:
- **Thread Automation**: Creates and manages token-specific threads in designated channels
- **Dynamic Thread Naming**: "(N) 🪿 │ TOKEN_SYMBOL" format showing participant count ("Goose score")
- **Real-time Updates**: Pool information and participant statistics
- **Anonymous Mode**: Track positions without sharing detailed information

**Commands**:
- `/lpfeed_register` - Register wallet
- `/lpfeed_unregister` - Remove wallet registration

### 2. LPArena Bot
An advanced bot for position sharing and community collaboration with privacy features.
Designed to facilitate sharing of wallet activity, positions, and strategies among liquidity providers, while maintaining privacy and anonymity.

**Key Features**:
- **Position Analytics**: Detailed tracking of opens, updates, and closes
- **Performance Metrics**: Fee earnings and position value calculations
- **Community Features**: Strategy sharing and discussion threads
- **Privacy Options**: Choose between detailed or anonymous updates
- **Voting System**: Predict position outcomes
- **Leaderboards**: Track community engagement and voting accuracy

**Commands**:
- `/lparena_register` - Register wallet with privacy options
- `/lparena_unregister` - Remove wallet registration
- `/lparena_leaderboard` - View global voting statistics
- `/lparena_user_stats` - Check personal or other user's statistics

## Technical Architecture

### Project Structure
```
├── bots/
│   ├── base/           # Common bot functionality
│   ├── lparena/        # LPArena bot implementation
│   └── lpfeed/         # LPFeed bot implementation
├── libs/
│   ├── meteora/        # Meteora IDL and utilities
│   ├── birdeye/        # Birdeye API wrapper
│   ├── helius/         # Helius API wrapper
│   ├── jupyter/        # Jupiter API integration
│   └── solana/         # Solana utilities
└── config/             # Configuration files
```

### Key Components
- **Meteora Integration**: libs/meteora/ contains reusable IDL definitions and utilities for Meteora development
- **External APIs**: Wrappers for Jupiter, Helius, and Birdeye services
- **Event Processing**: Helius webhooks for real-time position tracking
- **Fee Calculations**: Birdeye API integration for accurate fee value determination

## Setup Instructions

### Prerequisites
- Python 3.12+
- Discord Bot Token
- Helius API Key
- Solana RPC URL
- Birdeye API Key (for fee calculations)

### Installation
```
git clone https://github.com/madxbug/lpconnect.git
cd lpconnect
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Configuration

### Environment Configuration

- **`DISCORD_TOKEN`**: Required for bot authentication with Discord. Obtain it from the [Discord Developer Portal](https://discord.com/developers/applications) when creating a bot.

- **`NOTIFICATION_CHANNEL_ID`**: The main channel ID where the bot will post position updates and create threads. Enable Developer Mode in Discord, then right-click the channel and select "Copy ID."

- **`SOLANA_RPC`**: RPC endpoint for interacting with the Solana blockchain. Can be provided by services like [Helius](https://www.helius.dev/), [QuickNode](https://www.quicknode.com/), or your own Solana node.

- **`HELIUS_API_KEY`**: API key from Helius, used for webhook setup and enhanced RPC methods. Obtain it from your [Helius dashboard](https://dashboard.helius.dev/).

- **`HELIUS_WEBHOOK_ID`**: ID of the webhook created in the Helius UI. This is used to receive real-time notifications about wallet transactions.

- **`WEBHOOK_SERVER_HOST`**: Host address for the webhook server. Use `0.0.0.0` to accept connections from any IP address.

- **`WEBHOOK_SERVER_PORT`**: Port number for the webhook server. Ensure this port is open and accessible to Helius servers.

- **`STORAGE_DIR`**: Directory path where the bot stores its data (e.g., positions, user info). Default is `./data`.

---

#### **LPArena Specific Variables**

- **`ANONYMOUS_NOTIFICATIONS_CHANNEL_ID`**: Channel ID for anonymous position updates, embedded LPFeed functionality.

- **`CLEANUP_TIMEOUT`**: Time in seconds before session threads are closed when no open positions remain. Default is `60` seconds.

- **`BIRDEYE_API_KEY`**: API key from Birdeye, required for fetching price data to calculate claimed fee values. Obtain it from your [Birdeye dashboard](https://birdeye.so/).

---

**Note**: The bot requires manual webhook creation in the Helius UI. Refer to the [Helius Webhooks Documentation](https://docs.helius.dev/data-streaming/webhooks) for setup instructions.

---

### Example `.env` File

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token
NOTIFICATION_CHANNEL_ID=your_channel_id

# Solana Configuration
SOLANA_RPC=your_solana_rpc_url

# Helius Configuration
HELIUS_API_KEY=your_helius_api_key
HELIUS_WEBHOOK_ID=your_webhook_id

# Server Configuration
WEBHOOK_SERVER_HOST=0.0.0.0
WEBHOOK_SERVER_PORT=5000

# Storage
STORAGE_DIR=./data

# LPArena Specific
ANONYMOUS_NOTIFICATIONS_CHANNEL_ID=your_anonymous_channel_id
CLEANUP_TIMEOUT=60
BIRDEYE_API_KEY=your_birdeye_api_key
```

### Running the Bots
```
# Start LPArena Bot
python main.py lparena --env .env

# Start LPFeed Bot
python main.py lpfeed --env .env
```

## About Meteora
Meteora is a Solana-based DeFi platform featuring Dynamic Liquidity Market Maker (DLMM) technology. It enables real-time liquidity concentration and zero-slippage swaps for maximum capital efficiency.

For more information, visit [Meteora Documentation](https://docs.meteora.ag).

## Contributing
Contributions are welcome! For major changes, please open an issue first to discuss your proposed changes.

## License
This project is licensed under the MIT License.
