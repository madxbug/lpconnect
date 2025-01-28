import io

import numpy as np
from discord import Embed, File
from matplotlib import pyplot as plt

from bots.lparena.common import BLUE, ORANGE, GREEN, add_debug_info, PURPLE
from libs.meteora.idl.meteora_dllm.events.decoder import AddLiquidityEvent
from libs.utils.format import prettify_number
from libs.utils.utils import convert_value


def create_fee_claim_embed(position, claimed_fee_x, claimed_fee_y, position_index, event, token_x, token_y):
    embed = Embed(
        title=f"💰 Fee Claimed",
        color=PURPLE
    )
    embed.add_field(
        name="",
        value=(
            f"`{prettify_number(convert_value(claimed_fee_x, position.base_token_decimal))}` {token_x} \u002B "
            f"`{prettify_number(convert_value(claimed_fee_y, position.quote_token_decimal))}` {token_y}"
        ),
        inline=False
    )
    add_debug_info(embed, event)
    must_have_footer(embed, position, position_index)
    return embed


def create_position_update_embed(position, event, position_index, token_x, token_y):
    is_add = isinstance(event, AddLiquidityEvent)
    action = "Liquidity Added" if is_add else "Liquidity Removed"
    action_emoji = "💧" if is_add else "🔻"
    color = BLUE if is_add else ORANGE
    action_symbol = "＋" if is_add else "－"

    embed = Embed(
        title=f"{action_emoji} {action}",
        color=color
    )

    def format_token_change(amount, decimal, token_name):
        if amount <= 0:
            return ''
        value = convert_value(amount, decimal)
        return f"`{action_symbol}{prettify_number(value)}` {token_name}"

    token_changes = [
        format_token_change(event.amounts[1], position.quote_token_decimal, token_y),
        format_token_change(event.amounts[0], position.base_token_decimal, token_x)
    ]

    valid_changes = [change for change in token_changes if change]

    change_text = " | ".join(valid_changes)
    embed.add_field(
        name="",
        value=f"**Change:** {change_text}",
        inline=False
    )

    add_debug_info(embed, event)
    add_footer(embed, position, position_index, token_x, token_y)
    embed.set_image(url="attachment://chart.png")
    return embed


def create_new_position_embed(position, pair_data, token_x, token_y, thread, creator, event):
    embed = Embed(
        title=f"🏟️ `{creator}` Created {token_x}-{token_y} Position",
        color=GREEN
    )

    embed.add_field(
        name="",
        value=(
            f"**Range**: `{prettify_number(position.position_bin_data[0].price_per_token)}` - "
            f"`{prettify_number(position.position_bin_data[-1].price_per_token)}` "
            f"{token_y}/{token_x}\n"
            f"**Liquidity**: `{prettify_number(position.total_y_amount)}` {token_y} | "
            f"`{prettify_number(position.total_x_amount)}` {token_x}"
        ),
        inline=False
    )

    space = '\u2003\u2002'
    if pair_data:
        embed.add_field(
            name="⚙️ **Pool Setup**",
            value=(
                f"\u200B{space}**Bin Step**: `{pair_data.bin_step}`\n"
                f"{space}**Base Fee**: `{pair_data.base_fee_percentage}%`\n"
                f"{space}**Max Fee**: `{pair_data.max_fee_percentage}%`"
            ),
            inline=False
        )
        embed.add_field(
            name="📊 **Pool Info**",
            value=(
                f"\u200B{space}**Liquidity**: `${prettify_number(pair_data.liquidity)}`\n"
                f"{space}**24h Volume**: `${prettify_number(pair_data.trade_volume_24h)}`\n"
                f"{space}**24h Fees**: `${prettify_number(pair_data.fees_24h)}`\n"
            ),
            inline=False
        )

    embed.add_field(
        name="",
        value=f"💬 **Updates & Discussion**: [Thread]({thread.jump_url})\n\n" if thread else '\n',
        inline=False
    )

    add_debug_info(embed, event)
    must_have_footer(embed, position, 0)
    embed.set_image(url="attachment://chart.png")

    return embed


def create_secondary_position_embed(position, position_index, event, token_x, token_y):
    embed = Embed(
        title=f"🆕 Added Position #{position_index}",
        color=GREEN
    )
    add_debug_info(embed, event)
    add_footer(embed, position, position_index, token_x, token_y)
    embed.set_image(url="attachment://chart.png")

    return embed


def add_footer(embed, position, position_index, token_x, token_y):
    embed.add_field(
        name="",
        value=(
            f"**Range**: `{prettify_number(position.position_bin_data[0].price_per_token)}` - "
            f"`{prettify_number(position.position_bin_data[-1].price_per_token)}` "
            f"{token_y}/{token_x}"
        ),
        inline=False
    )
    embed.add_field(
        name="",
        value=(
            f"**Liquidity:** `{prettify_number(position.total_y_amount)}` {token_y} | "
            f"`{prettify_number(position.total_x_amount)}` {token_x}"
        ),
        inline=False
    )
    must_have_footer(embed, position, position_index)


def must_have_footer(embed, position, position_index):
    meteora_url = f"https://app.meteora.ag/dlmm/{position.info.position.lb_pair}"
    embed.add_field(name="", value=f"💥 [Meteora Pool]({meteora_url}) | Position #{position_index}", inline=False)
    embed.set_footer(text="LP Arena Bot 🤖 Powered by Meteora ☄️")


def find_representative_indices(bin_ids, x_amounts, y_amounts):
    total_bins = len(bin_ids)

    if total_bins == 1:
        return [0, 0, 0]

    any_liquidity_indices = np.where((x_amounts > 0) | (y_amounts > 0))[0]

    if len(any_liquidity_indices) == 0:
        return [0, 0, total_bins - 1]

    both_xy_indices = np.where((x_amounts > 0) & (y_amounts > 0))[0]

    if len(both_xy_indices) > 0:
        mid_index = both_xy_indices[len(both_xy_indices) // 2]
    elif any_liquidity_indices[0] == 0 and any_liquidity_indices[-1] == total_bins - 1:
        mid_index = total_bins // 2
    else:
        mid_index = any_liquidity_indices[0] if any_liquidity_indices[0] > 0 else any_liquidity_indices[-1]

    return [0, min(any_liquidity_indices), mid_index, max(any_liquidity_indices), total_bins - 1]


positions_history = {}


async def create_chart(position, position_address: str):
    # Get current position data
    bin_ids = np.array([d.bin_id for d in position.position_bin_data])
    prices = np.array([d.price_per_token for d in position.position_bin_data])
    x_amounts = np.array([d.position_x_amount for d in position.position_bin_data])
    y_amounts = np.array([d.position_y_amount for d in position.position_bin_data])

    x_heights = x_amounts * prices
    total_heights = y_amounts + x_heights

    scheme = {
        "x": "#FF6B6B",
        "y": "#4ECDC4",
        "delta": "#9D4EDD",  # Purple for changes
        "bg": "#1E2130",
        "text": "#FFFFFF"
    }

    fig, ax = plt.subplots(figsize=(12, 6))

    # Draw current position
    ax.bar(bin_ids, total_heights, width=0.8, color=scheme['y'], edgecolor='none')
    ax.bar(bin_ids, x_heights, width=0.8, color=scheme['x'], edgecolor='none')

    # Draw deltas if we have history
    if position_address in positions_history:
        prev_data = positions_history[position_address]
        prev_bin_ids = np.array([d.bin_id for d in prev_data.position_bin_data])
        prev_x_amounts = np.array([d.position_x_amount for d in prev_data.position_bin_data])
        prev_y_amounts = np.array([d.position_y_amount for d in prev_data.position_bin_data])

        prev_x_heights = prev_x_amounts * prices
        prev_total_heights = prev_y_amounts + prev_x_heights

        # Draw delta bars
        for i, bin_id in enumerate(bin_ids):
            prev_idx = np.where(prev_bin_ids == bin_id)[0]
            if len(prev_idx) > 0:
                prev_idx = prev_idx[0]
                delta = total_heights[i] - prev_total_heights[prev_idx]

                if delta > 0:
                    # Growth: draw from old height
                    ax.bar(bin_id, delta, bottom=prev_total_heights[prev_idx],
                           width=0.8, color=scheme['delta'], edgecolor='none', alpha=0.5)
                elif delta < 0:
                    # Decrease: draw from new height
                    ax.bar(bin_id, abs(delta), bottom=total_heights[i],
                           width=0.8, color=scheme['delta'], edgecolor='none', alpha=0.5)

    # Rest of the styling remains the same
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.yaxis.set_visible(False)

    representative_indices = find_representative_indices(bin_ids, x_amounts, y_amounts)
    ax.set_xticks([bin_ids[i] for i in representative_indices])
    ax.set_xticklabels([f"{prices[i]:.9f}" for i in representative_indices],
                       rotation=45, ha='right', color=scheme['text'])

    fig.patch.set_facecolor(scheme['bg'])
    ax.set_facecolor(scheme['bg'])
    ax.tick_params(colors=scheme['text'])

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=scheme['bg'], edgecolor='none')
    buf.seek(0)
    plt.close(fig)

    positions_history[position_address] = position
    return File(buf, filename="chart.png")
