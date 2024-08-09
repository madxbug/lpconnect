import io

import numpy as np
from discord import Embed, File
from matplotlib import pyplot as plt

from meteora.pair_data import PairData
from utils.format import prettify_number

ORANGE = 0xff4d04
GREEN = 0x00ff00
RED = 0xff0000
POSITION_CREATE = "created"
POSITION_UPDATE = "updated"
update_type2color = {
    POSITION_CREATE: GREEN,
    POSITION_UPDATE: ORANGE
}


async def send_position_embed(channel, position, pair_data, token_info, update_type):
    embed = create_embed(position, pair_data, token_info, update_type)
    chart_file = await create_chart(position)

    try:
        return await channel.send(embed=embed, file=chart_file)
    except Exception as e:
        print(f"Error sending embed: {e}")
        return None


def create_embed(position, pair_data, token_info, update_type):
    embed = Embed(title=f"Position {update_type}: {pair_data.name}", color=update_type2color[update_type])

    owner_address = str(position.info.position.owner)
    short_name = f"{owner_address[:4]}...{owner_address[-4:]}"

    embed.add_field(name="\u200b",
                    value=f"**Wallet** [{short_name}](https://alpha.vybenetwork.com/wallets/"
                          f"{owner_address}?tab=activity)",
                    inline=False)

    embed.add_field(name="Pool Info", value=(
        f"Bin Step: `{pair_data.bin_step}` | "
        f"Base Fee: `{pair_data.base_fee_percentage}%` | "
        f"Max Fee: `{pair_data.max_fee_percentage}%`"
    ), inline=False)

    embed.add_field(name="Pool Data", value=(
        f"Liquidity: `${prettify_number(pair_data.liquidity)}`\n"
        f"[24h] Volume | Fees: "
        f"`${prettify_number(pair_data.trade_volume_24h)}` | `${prettify_number(pair_data.fees_24h)}`\n"
        f"Current Price: `{prettify_number(token_info.price)} {token_info.name_y} per {token_info.name_x}`"
    ), inline=False)

    embed.add_field(name="Position Liquidity", value=(
        f"`{prettify_number(position.total_x_amount)}` {token_info.name_x} | "
        f"`{prettify_number(position.total_y_amount)}` {token_info.name_y}"
    ), inline=False)

    embed.add_field(name="Active Range",
                    value=f"{position.position_bin_data[0].price_per_token:.9f} - "
                          f"{position.position_bin_data[-1].price_per_token:.9f}",
                    inline=True)

    birdeye_url = (f"https://birdeye.so/token/{position.lb_pair_info.token_x_mint}/"
                   f"{position.info.position.lb_pair}?chain=solana")
    meteora_url = f"https://app.meteora.ag/dlmm/{position.info.position.lb_pair}"
    lp4fun_url = f"https://lp4fun.vercel.app/position/{position.info.public_key}"

    embed.add_field(name="Links", value=(
        f"[Birdeye]({birdeye_url}) | "
        f"[Meteora]({meteora_url}) | "
        f"[LP4Fun]({lp4fun_url})"
    ), inline=False)

    embed.set_image(url="attachment://chart.png")

    return embed


def find_representative_indices(bin_ids, x_amounts, y_amounts):
    if len(bin_ids) == 1:
        return [0, 0, 0]

    both_xy_indices = np.where((x_amounts > 0) & (y_amounts > 0))[0]
    if len(both_xy_indices) > 0:
        mid_index = both_xy_indices[len(both_xy_indices) // 2]
    else:
        any_liquidity_indices = np.where((x_amounts > 0) | (y_amounts > 0))[0]
        if len(any_liquidity_indices) > 0:
            mid_index = any_liquidity_indices[len(any_liquidity_indices) // 2]
        else:
            mid_index = len(bin_ids) // 2

    return [0, mid_index, len(bin_ids) - 1]


async def create_chart(position):
    bin_ids = np.array([d.bin_id for d in position.position_bin_data])
    prices = np.array([d.price_per_token for d in position.position_bin_data])
    x_amounts = np.array([d.position_x_amount for d in position.position_bin_data])
    y_amounts = np.array([d.position_y_amount for d in position.position_bin_data])

    x_heights = x_amounts * prices
    total_heights = y_amounts + x_heights

    scheme = {"x": "#FF6B6B", "y": "#4ECDC4", "bg": "#1E2130", "text": "#FFFFFF"}

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(bin_ids, total_heights, width=0.8, color=scheme['y'], edgecolor='none')
    ax.bar(bin_ids, x_heights, width=0.8, color=scheme['x'], edgecolor='none')

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

    return File(buf, filename="chart.png")


async def send_position_close_embed(channel, owner_pubkey,
                                    position_public_key, pair_data: PairData):
    embed = Embed(title=f"Position Closed: {pair_data.name}", color=RED)
    owner_address = str(owner_pubkey)
    short_name = f"{owner_address[:4]}...{owner_address[-4:]}"
    embed.add_field(name="\u200b",
                    value=f"**Wallet** [{short_name}](https://alpha.vybenetwork.com/wallets/"
                          f"{owner_address}?tab=activity)", inline=False)

    birdeye_url = (f"https://birdeye.so/token/{pair_data.mint_x}/"
                   f"{pair_data.address}?chain=solana")
    meteora_url = f"https://app.meteora.ag/dlmm/{pair_data.address}"
    lp4fun_url = f"https://lp4fun.vercel.app/position/{position_public_key}"

    embed.add_field(name="Links", value=(
        f"[Birdeye]({birdeye_url}) | "
        f"[Meteora]({meteora_url}) | "
        f"[LP4Fun]({lp4fun_url})"
    ), inline=False)

    return await channel.send(embed=embed)
