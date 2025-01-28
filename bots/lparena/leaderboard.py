from io import BytesIO

import discord
import pandas as pd

from libs.utils.format import prettify_number


async def generate_leaderboard(vote_manager, discord_client, limit=10):
    """
    Generate a Discord embed and CSV file for the leaderboard
    """
    leaderboard = await vote_manager.get_leaderboard(limit=limit)

    # Create the main embed
    embed = discord.Embed(
        title="🏆 Global Leaderboard",
        description="Top performers across all voting sessions",
        color=discord.Color.gold()
    )

    if not leaderboard:
        embed.add_field(name="No Data", value="No voting history available yet.", inline=False)
        return embed, None

    # Calculate some overall statistics
    total_users = len(leaderboard)
    total_points = sum(user['total_points'] for user in leaderboard)
    avg_accuracy = sum(user['accuracy'] for user in leaderboard) / total_users if total_users > 0 else 0

    # Add overall statistics
    embed.add_field(name="Total Users", value=str(total_users), inline=True)
    embed.add_field(name="Total Points", value=f"{prettify_number(total_points)}", inline=True)
    embed.add_field(name="Avg Accuracy", value=f"{avg_accuracy:.2%}", inline=True)

    # Create the leaderboard text
    leaderboard_text = ""
    csv_data = []

    for rank, user in enumerate(leaderboard, 1):
        # Fetch Discord user info
        discord_user = await discord_client.fetch_user(user['user_id'])

        # Add to leaderboard text
        leaderboard_text += (
            f"{get_rank_emoji(rank)} <@{discord_user.id}>: **{prettify_number(user['total_points'])}** points\n"
            f"└ 📊 {user['correct_votes']}/{user['correct_votes'] + user['incorrect_votes']} "
            f"correct ({user['accuracy']:.1%})\n\n"
        )

        # Add to CSV data
        csv_data.append({
            'Rank': rank,
            'User Name': discord_user.name,
            'User ID': user['user_id'],
            'Total Points': user['total_points'],
            'Correct Votes': user['correct_votes'],
            'Incorrect Votes': user['incorrect_votes'],
            'Accuracy': user['accuracy']
        })

    # Add the leaderboard text to the embed
    embed.add_field(name="Top Performers", value=leaderboard_text, inline=False)

    # Create CSV file
    df = pd.DataFrame(csv_data)
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    csv_file = discord.File(csv_buffer, filename="leaderboard.csv")

    return embed, csv_file


def get_rank_emoji(rank):
    """Return appropriate emoji for the rank"""
    if rank == 1:
        return "👑"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    else:
        return f"{rank}."


async def send_leaderboard(self, channel):
    """
    Send leaderboard to a Discord channel
    """
    try:
        embed, csv_file = await generate_leaderboard(self.vote_storage, self.discord_client)
        await channel.send(
            content="📊 **Current Voting Leaderboard**",
            embed=embed,
            file=csv_file if csv_file else None
        )
    except Exception as e:
        print(f"Error generating leaderboard: {e}")
        await channel.send("❌ Failed to generate leaderboard.")
