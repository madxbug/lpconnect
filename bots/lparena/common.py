import io
from datetime import datetime
from io import BytesIO

import discord
import pandas as pd
from discord import Embed
from matplotlib import pyplot as plt

from bots.base.database.position_performance_manager import PositionPerformance
from libs.utils.format import prettify_number

BLUE = 0x0000ff
PURPLE = 0x9932cc
ORANGE = 0xff4d04
GREEN = 0x00ff00
RED = 0xff0000
GOLD = 0xffd700
POSITION_CREATE = "created"
POSITION_UPDATE = "updated"

debug = False


def add_debug_info(embed, event):
    global debug
    if debug:
        embed.add_field(
            name="",
            value=(
                f"🐞: {event.tx}"
            ),
            inline=False
        )


def generate_performance_table(performance: PositionPerformance, name_x: str, name_y: str):
    profit = performance.withdrawals.value_in_y + performance.fees_earned.value_in_y - performance.deposits.value_in_y

    data = [
        ['Deposits', prettify_number(performance.deposits.amount_y), prettify_number(performance.deposits.amount_x),
         prettify_number(performance.deposits.value_in_y)],
        ['Withdrawals', prettify_number(performance.withdrawals.amount_y),
         prettify_number(performance.withdrawals.amount_x), prettify_number(performance.withdrawals.value_in_y)],
        ['Fees Earned', prettify_number(performance.fees_earned.amount_y),
         prettify_number(performance.fees_earned.amount_x), prettify_number(performance.fees_earned.value_in_y)],
        ['Profit', prettify_number(
            performance.withdrawals.amount_y + performance.fees_earned.amount_y - performance.deposits.amount_y),
         prettify_number(
             performance.withdrawals.amount_x + performance.fees_earned.amount_x - performance.deposits.amount_x),
         prettify_number(profit)]
    ]
    columns = ['', f'Amount ({name_y})', f'Amount ({name_x})', f'Value ({name_y})']

    if profit > 0:
        background_color = '#b3ffb3'  # Light green
    elif profit < 0:
        background_color = '#ffb3b3'  # Light red
    else:
        background_color = '#ffffb3'  # Light yellow

    fig, ax = plt.subplots(figsize=(7, 2.2), dpi=100, facecolor=background_color)
    ax.set_facecolor(background_color)
    ax.axis('off')

    text_color = '#333333'
    header_color = '#007aff'

    table = ax.table(cellText=data, colLabels=columns, loc='center', cellLoc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('none')
        if row == 0:
            cell.set_text_props(weight='bold', color=header_color)
        else:
            cell.set_text_props(color=text_color)
        cell.set_facecolor(background_color)

    for key, cell in table.get_celld().items():
        cell.set_linewidth(0)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_linewidth(0)
        else:
            cell.set_linewidth(0.1)
            cell.set_edgecolor('#d0d0d0')

    plt.tight_layout(pad=0.4)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, facecolor=background_color, edgecolor='none',
                dpi=100)
    buf.seek(0)
    plt.close(fig)

    return buf


def create_position_close_embed(performance: PositionPerformance,
                                position_index: int, create_event_block_time: int, event, token_x, token_y):
    profit = performance.withdrawals.value_in_y + performance.fees_earned.value_in_y - performance.deposits.value_in_y
    sign = ''
    if profit > 0:
        sign = '+'
    elif profit < 0:
        sign = '-'

    embed = Embed(
        title=f"🎯 Closed Position #{position_index}",
        description=f"Net Profit is **{sign}{prettify_number(abs(profit))}** {token_y}",
        color=RED
    )
    embed.add_field(name="", value=f"Duration: {format_time_distance(create_event_block_time)}", inline=False)
    add_debug_info(embed, event)
    table_image = generate_performance_table(performance, token_x, token_y)
    embed.set_image(url="attachment://performance_table.png")
    embed.set_footer(text="LP Arena Bot 🤖 Powered by Meteora ☄️")

    return embed, table_image


def create_session_close_embed(performance: PositionPerformance, token_x, token_y):
    # FIXME add duration and entry/exit price and value in USD + % profit
    profit = performance.withdrawals.value_in_y + performance.fees_earned.value_in_y - performance.deposits.value_in_y
    sign = ''
    if profit > 0:
        sign = '+'
    elif profit < 0:
        sign = '-'

    embed = Embed(
        title=f"🏁 Final results",
        description=f"Net Profit is **{sign}{prettify_number(abs(profit))}** {token_y}",
        color=GOLD
    )
    table_image = generate_performance_table(performance, token_x, token_y)
    embed.set_image(url="attachment://performance_table.png")
    embed.set_footer(text="LP Arena Bot 🤖 Powered by Meteora ☄️")
    return embed, table_image


def format_time_distance(start_seconds):
    start_time = datetime.fromtimestamp(start_seconds)
    now = datetime.now()
    diff = now - start_time

    total_seconds = int(diff.total_seconds())

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    parts.append(f"{hours}h:{minutes:02}m:{seconds:02}s")

    return ', '.join(parts) if parts else '0s'


async def generate_vote_summary(vote_details, discord_client, actual_outcome):
    sorted_votes = sorted(vote_details, key=lambda x: x['points'], reverse=True)

    total_votes = len(sorted_votes)
    correct_votes = sum(1 for vote in sorted_votes if vote['vote'] == actual_outcome)
    accuracy = (correct_votes / total_votes) * 100 if total_votes > 0 else 0

    embed = discord.Embed(title="🗳️ Voting Results Summary", color=discord.Color.blue())
    embed.add_field(name="Total Votes", value=str(total_votes), inline=True)
    embed.add_field(name="Correct Votes", value=str(correct_votes), inline=True)
    embed.add_field(name="Accuracy", value=f"{accuracy:.2f}%", inline=True)

    if total_votes > 0:
        top_voters = "Top 5 Voters:\n"
        for i, vote in enumerate(sorted_votes[:5], 1):
            user = await discord_client.fetch_user(vote['user_id'])
            top_voters += f"{i}. <@{user.id}>: {vote['vote']} ({prettify_number(vote['points'])} points)\n"
        embed.add_field(name="Top Performers", value=top_voters, inline=False)
    else:
        embed.add_field(name="Top Performers", value="No votes recorded for this position.", inline=False)

    csv_data = []
    for vote in sorted_votes:
        user = await discord_client.fetch_user(vote['user_id'])
        csv_data.append(
            {'User Name': user.name, 'User ID': vote['user_id'], 'Vote': vote['vote'], 'Points': vote['points']})

    df = pd.DataFrame(csv_data)
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    csv_file = discord.File(csv_buffer, filename="vote_results.csv")

    return embed, csv_file if total_votes > 0 else None
