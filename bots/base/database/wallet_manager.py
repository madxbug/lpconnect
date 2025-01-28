import logging

from bots.base.database.wallet_db import WalletStorage
from config.constants import LPCONNECT
from libs.helius.helius_webhook_api import HeliusWebhookAPI


class WalletManager:
    """Manages wallet registration and synchronization between WalletStorage and HeliusWebhookAPI."""

    logger = logging.getLogger(LPCONNECT)

    def __init__(self, webhook_api: HeliusWebhookAPI, db: WalletStorage, webhook_id: str):
        if webhook_id is None:
            raise Exception('Missing webhook_id during WalletManager initialization')
        self.webhook_api = webhook_api
        self.db = db
        self.webhook_id = webhook_id
        self.logger.info(f"Initialized WalletManager with webhook {webhook_id}")

    async def register_wallet(self, discord_id: str, wallet_address: str, is_anonymous: bool) -> bool:
        """Register wallet in database and webhook with rollback on failure."""
        try:
            db_success = await self.db.add_wallet(discord_id, wallet_address, is_anonymous)
            if not db_success:
                self.logger.info(f"Wallet {wallet_address} already exists for user {discord_id}")
                return False

            try:
                self.webhook_api.append_addresses_to_webhook(
                    self.webhook_id,
                    [wallet_address]
                )
                self.logger.info(f"Successfully registered wallet {wallet_address} for user {discord_id}")
                return True
            except Exception as e:
                self.logger.error(f"Webhook registration failed for {wallet_address}: {str(e)}")
                await self.db.remove_wallet(discord_id, wallet_address)
                raise Exception(f"Failed to add wallet to webhook: {str(e)}")

        except Exception as e:
            self.logger.error(f"Registration failed for {wallet_address}: {str(e)}")
            raise Exception(f"Error during wallet registration: {str(e)}")

    async def unregister_wallet(self, discord_id: str, wallet_address: str) -> bool:
        """Unregister wallet from database and webhook."""
        try:
            db_success = await self.db.remove_wallet(discord_id, wallet_address)
            if not db_success:
                self.logger.info(f"Wallet {wallet_address} not found for user {discord_id}")
                return False

            try:
                self.webhook_api.remove_addresses_from_webhook(
                    self.webhook_id,
                    [wallet_address]
                )
                self.logger.info(f"Successfully unregistered wallet {wallet_address} for user {discord_id}")
                return True
            except Exception as e:
                self.logger.error(f"Webhook unregistration failed for {wallet_address}: {str(e)}")
                raise Exception(f"Failed to remove wallet from webhook: {str(e)}")

        except Exception as e:
            self.logger.error(f"Unregistration failed for {wallet_address}: {str(e)}")
            raise Exception(f"Error during wallet unregistration: {str(e)}")

    async def sync_webhook_with_db(self) -> None:
        """Sync webhook addresses with database records."""
        try:
            all_wallets = await self.db.get_all_wallets()
            if not all_wallets:
                return
            self.webhook_api.edit_webhook(
                self.webhook_id,
                accountAddresses=all_wallets
            )
            self.logger.info(f"Synced {len(all_wallets)} wallets with webhook {self.webhook_id}")
            for wallet in all_wallets:
                self.logger.info(f"Synced wallet: {wallet}")
        except Exception as e:
            self.logger.error(f"Webhook sync failed: {str(e)}")
            raise Exception(f"Error during webhook synchronization: {str(e)}")
