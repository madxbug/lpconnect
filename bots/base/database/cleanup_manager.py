import logging

import discord

from bots.lparena.common import generate_vote_summary, create_session_close_embed
from config.constants import LPCONNECT

logger = logging.getLogger(LPCONNECT)


class CleanupManager:
    def __init__(self, position_index_manager, position_performance_manager, vote_manager, token_manager,
                 discord_client):
        self.position_index_manager = position_index_manager
        self.position_performance_manager = position_performance_manager
        self.vote_manager = vote_manager
        self.token_manager = token_manager
        self.discord_client = discord_client

    async def cleanup_session(self, discord_channel, thread_id, lb_pair, owner, main_message_id,
                              placeholder_message_id):
        thread = discord_channel.get_thread(thread_id)

        await self.position_index_manager.cleanup_lb_pair_positions(lb_pair, owner)
        performance = await self.position_performance_manager.get_aggregated_user_lbpair_performance(owner, thread_id,
                                                                                                     lb_pair)
        token_x, token_y = await self.token_manager.get_tokens(lb_pair)
        profit = performance.withdrawals.value_in_y + performance.fees_earned.value_in_y - performance.deposits.value_in_y
        actual_outcome = '🟢' if profit > 0 else '🔴'
        await self.vote_manager.set_vote_result(main_message_id, actual_outcome, is_final=True)
        try:
            vote_details = await self.vote_manager.get_vote_details(main_message_id)
            summary_embed, csv_file = await generate_vote_summary(vote_details, self.discord_client, actual_outcome)
            await thread.send(embed=summary_embed, file=csv_file)
        except Exception as e:
            logging.exception(f'Failed to generate vote summary {e}')
        embed, table_image = create_session_close_embed(performance, token_x, token_y)
        await thread.send(file=discord.File(table_image, filename="performance_table.png"), embed=embed)
        await thread.send("🌊 Session closed. Next wave awaits! 🌪️")
        if placeholder_message_id:
            try:
                placeholder_message = await discord_channel.fetch_message(placeholder_message_id)
                await placeholder_message.edit(embed=embed, content=None)
            except discord.errors.NotFound:
                print(f"Placeholder message with ID {placeholder_message_id} not found")
