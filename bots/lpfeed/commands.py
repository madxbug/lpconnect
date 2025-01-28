import logging
import traceback

import discord
from discord import app_commands
from solders.pubkey import Pubkey

from bots.base.database.wallet_manager import WalletManager
from bots.base.database.wallet_manager import WalletStorage
from config.constants import LPCONNECT

logger = logging.getLogger(LPCONNECT)


def setup_commands(tree: app_commands.CommandTree,
                   wallet_manager: WalletManager,
                   wallet_storage: WalletStorage):
    @tree.command(name="lpfeed_register", description="🚀 Join the LPFeed: Register your wallet")
    async def wallet_registration(interaction: discord.Interaction):
        wallet_input = discord.ui.TextInput(
            label="🔑 Your Solana Wallet Address",
            placeholder="Enter your Solana wallet address here...",
            style=discord.TextStyle.short,
            min_length=32,
            max_length=44,
            required=True
        )

        class RegistrationModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="🌟 LPFeed Wallet Registration")
                self.add_item(wallet_input)

            async def on_submit(self, interaction: discord.Interaction):
                # First, acknowledge the interaction within 3 seconds
                await interaction.response.defer(ephemeral=True)

                try:
                    wallet_address = wallet_input.value.strip()

                    try:
                        Pubkey.from_string(wallet_address)
                    except ValueError:
                        await interaction.followup.send(
                            "⚠️ The wallet address format is invalid. Please check and try again.",
                            ephemeral=True
                        )
                        return

                    exists = await wallet_storage.wallet_exists(wallet_address)
                    if exists:
                        await interaction.followup.send(
                            "ℹ️ This wallet is already registered.",
                            ephemeral=True
                        )
                        return

                    success = await wallet_manager.register_wallet(
                        str(interaction.user.id),
                        wallet_address,
                        is_anonymous=True
                    )

                    if success:
                        await interaction.followup.send(
                            f"🎉 Success, {interaction.user.mention}! Your wallet has been registered:\n"
                            f"```\n{wallet_address}\n```\n"
                            f"Monitoring will begin shortly.",
                            ephemeral=True
                        )
                    else:
                        await interaction.followup.send(
                            "❌ Registration failed. Please try again later.",
                            ephemeral=True
                        )

                except Exception as e:
                    logger.error(f"Registration error: {e}")
                    traceback.print_exc()
                    await interaction.followup.send(
                        "❌ Something went wrong during registration. Please try again.",
                        ephemeral=True
                    )

        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

    @tree.command(name="lpfeed_unregister", description="🔄 Unregister your wallet from LPFeed")
    async def wallet_unregistration(interaction: discord.Interaction):
        wallets = await wallet_storage.get_user_wallets(str(interaction.user.id))
        if not wallets:
            await interaction.response.send_message("❌ No registered wallets found.", ephemeral=True)
            return

        options = [discord.SelectOption(label=w[:8] + "..." + w[-4:], value=w) for w in wallets]
        select = discord.ui.Select(
            placeholder="Choose wallet to unregister",
            options=options,
            custom_id="wallet_select"
        )

        async def select_callback(interaction: discord.Interaction):
            try:
                wallet_address = select.values[0]
                success = await wallet_manager.unregister_wallet(str(interaction.user.id), wallet_address)

                if success:
                    await interaction.response.send_message(
                        f"✅ Unregistered wallet:\n```\n{wallet_address}\n```",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message("❌ Failed to unregister wallet.", ephemeral=True)

            except Exception as e:
                logger.error(f"Unregistration error: {e}")
                await interaction.response.send_message("❌ Unregistration failed. Please try again.", ephemeral=True)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Select wallet to unregister:", view=view, ephemeral=True)
