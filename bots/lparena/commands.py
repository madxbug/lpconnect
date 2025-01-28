import logging
import traceback
from typing import Optional

import discord
from discord import app_commands
from solders.pubkey import Pubkey

from bots.base.database.vote_manager import VoteStorage
from bots.base.database.wallet_manager import WalletManager
from bots.base.database.wallet_manager import WalletStorage
from bots.lparena.leaderboard import generate_leaderboard
from config.constants import LPCONNECT
from libs.utils.format import prettify_number

logger = logging.getLogger(LPCONNECT)


def setup_commands(tree: app_commands.CommandTree,
                   wallet_manager: WalletManager,
                   wallet_storage: WalletStorage,
                   vote_storage: VoteStorage,
                   discord_client: discord.Client):
    @tree.command(name="lparena_register", description="🚀 Join the LPArena: Register your wallet")
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
                super().__init__(title="🌟 LPArena Wallet Registration")
                self.add_item(wallet_input)

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    await interaction.response.send_message(
                        "**Choose how your activity is shared:**\n\n"
                        "🔍 **Detailed Updates**: Your liquidity activity (adding/removing) will be visible in updates. "
                        "(Your wallet address and transaction details remain hidden, but your Discord name will be shown.)\n"
                        "📊 **Anonymous Mode**: Your activity will only count towards overall statistics. "
                        "No individual updates or details will be shared.\n",
                        view=VisibilitySelectionView(wallet_input.value.strip()),
                        ephemeral=True
                    )
                except Exception as e:
                    logger.error(f"Modal submission error: {e}")
                    traceback.print_exc()
                    await interaction.response.send_message(
                        "❌ An error occurred. Please try again later.",
                        ephemeral=True
                    )

        class VisibilitySelectionView(discord.ui.View):
            def __init__(self, wallet_address: str):
                super().__init__(timeout=60)
                self.wallet_address = wallet_address
                self.processing = False

            @discord.ui.button(label="Detailed Updates", style=discord.ButtonStyle.primary, emoji="🔍")
            async def detailed_updates(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.processing:
                    return
                self.processing = True
                # Disable both buttons
                for child in self.children:
                    child.disabled = True
                button.label = "Processing..."
                await interaction.response.edit_message(view=self)
                await self.process_registration(interaction, is_anonymous=False)

            @discord.ui.button(label="Anonymous Mode", style=discord.ButtonStyle.secondary, emoji="🕶️")
            async def anonymous_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.processing:
                    return
                self.processing = True
                # Disable both buttons
                for child in self.children:
                    child.disabled = True
                button.label = "Processing..."
                await interaction.response.edit_message(view=self)
                await self.process_registration(interaction, is_anonymous=True)

            async def process_registration(self, interaction: discord.Interaction, is_anonymous: bool):
                try:
                    try:
                        Pubkey.from_string(self.wallet_address)
                    except ValueError:
                        await interaction.followup.send(
                            "⚠️ The wallet address format is invalid. Please check and try again.", ephemeral=True)
                        return

                    exists = await wallet_storage.wallet_exists(self.wallet_address)
                    if exists:
                        await interaction.followup.send("ℹ️ This wallet is already registered.", ephemeral=True)
                        return

                    success = await wallet_manager.register_wallet(
                        str(interaction.user.id),
                        self.wallet_address,
                        is_anonymous=is_anonymous
                    )

                    if success:
                        visibility_mode = "🕶️ Anonymous Mode" if is_anonymous else "🔍 Detailed Updates Mode"
                        description = (
                            "Your activities will only be included in overall statistics." if is_anonymous
                            else "Your liquidity activities will be shared in updates (wallet address and transaction details are hidden)."
                        )

                        await interaction.followup.send(
                            f"🎉 Success, {interaction.user.mention}! Your wallet has been registered in {visibility_mode}:\n"
                            f"```\n{self.wallet_address}\n```\n"
                            f"ℹ️ {description}\n"
                            f"Monitoring will begin shortly.",
                            ephemeral=True
                        )
                    else:
                        await interaction.followup.send("❌ Registration failed. Please try again later.",
                                                        ephemeral=True)

                except Exception as e:
                    logger.error(f"Registration error: {e}")
                    traceback.print_exc()
                    await interaction.followup.send("❌ Something went wrong during registration. Please try again.",
                                                    ephemeral=True)
                finally:
                    self.stop()

        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

    @tree.command(name="lparena_unregister", description="🔄 Unregister your wallet from LPArena")
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

    @tree.command(name="lparena_leaderboard", description="📊 View the LPArena voting leaderboard")
    async def show_leaderboard(interaction: discord.Interaction):
        """Show the global voting leaderboard"""
        try:
            await interaction.response.defer(ephemeral=True)  # Make the initial response ephemeral

            # Generate leaderboard
            embed, csv_file = await generate_leaderboard(vote_storage, discord_client)

            # Send the response with both embed and CSV file
            await interaction.followup.send(
                content="📊 **Current Voting Leaderboard**",
                embed=embed,
                ephemeral=True  # Make the followup message ephemeral
            )

        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            logger.error(traceback.format_exc())

            if interaction.response.is_done():
                await interaction.followup.send("❌ Failed to generate leaderboard. Please try again later.",
                                                ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to generate leaderboard. Please try again later.",
                                                        ephemeral=True)

    @tree.command(name="lparena_user_stats", description="📈 View your or another user's voting statistics")
    @app_commands.describe(user="The user to view stats for (leave empty for your own stats)")
    async def show_user_stats(interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Show detailed statistics for a specific user"""
        try:
            await interaction.response.defer(ephemeral=True)

            target_user = user if user else interaction.user
            basic_stats = await vote_storage.get_user_stats(target_user.id)
            detailed_stats = await vote_storage.get_user_voting_stats(target_user.id)

            # Check if user has any activity
            has_voted = basic_stats['correct_votes'] > 0 or basic_stats['incorrect_votes'] > 0
            has_created = detailed_stats['created_votes']['total'] > 0

            if not has_voted and not has_created:
                await interaction.followup.send(
                    f"📊 {target_user.mention} hasn't participated in or created any votes yet!",
                    ephemeral=True
                )
                return

            embed = discord.Embed(
                title=f"📊 Voting Statistics for {target_user.display_name}",
                color=discord.Color.blue()
            )

            # Voting Activity Section
            if has_voted:
                total_votes = basic_stats['correct_votes'] + basic_stats['incorrect_votes']
                voting_stats = [
                    f"🎯 **Accuracy:** {basic_stats['accuracy']:.1%}",
                    f"✅ **Correct:** {basic_stats['correct_votes']}",
                    f"❌ **Incorrect:** {basic_stats['incorrect_votes']}",
                    f"⭐ **Total Points:** {prettify_number(basic_stats['total_points'])}",
                    f"📊 **Average Points:** {detailed_stats['voting_activity']['average_points']:.2f}",
                    f"⚖️ **Average Weight:** {detailed_stats['voting_activity']['average_weight']:.2f}"
                ]

                if detailed_stats['voting_activity']['average_response_time']:
                    avg_response = detailed_stats['voting_activity']['average_response_time']
                    voting_stats.append(f"⚡ **Avg Response:** {avg_response:.1f}s")

                embed.add_field(
                    name=f"🗳️ Voting Activity ({total_votes} votes)",
                    value="\n".join(voting_stats),
                    inline=False
                )

            # Vote Creation Section
            if has_created:
                created_total = detailed_stats['created_votes']['total']
                resolved = detailed_stats['created_votes']['resolved']
                pending = created_total - resolved

                creation_stats = [
                    f"📬 **Total Created:** {created_total}",
                    f"✅ **Resolved:** {resolved}",
                    f"⏳ **Pending:** {pending}"
                ]

                embed.add_field(
                    name="🎲 Created Votes",
                    value="\n".join(creation_stats),
                    inline=False
                )

            # Timeline Info
            if has_voted and detailed_stats['voting_activity']['first_vote']:
                first_vote = detailed_stats['voting_activity']['first_vote'].strftime('%Y-%m-%d')
                last_vote = detailed_stats['voting_activity']['last_vote'].strftime('%Y-%m-%d')
                if first_vote != last_vote:
                    embed.set_footer(text=f"Active since {first_vote} • Last vote: {last_vote}")
                else:
                    embed.set_footer(text=f"Started voting: {first_vote}")

            await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error showing user stats: {e}")
            logger.error(traceback.format_exc())

            if interaction.response.is_done():
                await interaction.followup.send("❌ Failed to retrieve user statistics. Please try again later.",
                                                ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to retrieve user statistics. Please try again later.",
                                                        ephemeral=True)
