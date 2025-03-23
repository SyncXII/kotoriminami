import os
import discord
import random
import asyncio
import requests
from discord.ext import commands, tasks
from discord import app_commands

# Load environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
MENTION_ID = int(os.getenv("DISCORD_USER_ID"))

# Set up bot
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Slash commands handler

# Forum URL
FORUM_URL = "https://phcorner.org/forums/freemium-access.261/"

# Fake cookie (Replace with a valid session cookie if needed)
COOKIES = {
    "xf_user": "your_cookie_here"
}

# Store seen threads to avoid duplicate notifications
seen_threads = set()

# Mention user on bot startup
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"⚠️ Error syncing commands: {e}")

    # Mention user in the channel when bot starts
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"✅ Bot started! <@{MENTION_ID}>")

# Scrape latest threads
def scrape_latest_threads():
    try:
        response = requests.get(FORUM_URL, cookies=COOKIES)
        response.raise_for_status()
        # Simulate parsing threads (Replace with real logic)
        threads = [{"title": f"Thread {i}", "author": "kotoriminami", "link": f"https://phcorner.org/thread{i}"} for i in range(1, 6)]
        return threads
    except Exception as e:
        print(f"⚠️ Error scraping: {e}")
        return []

# Task to check for new threads
@tasks.loop(seconds=5)
async def check_for_new_threads():
    threads = scrape_latest_threads()
    if not threads:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    for thread in threads:
        if thread["author"] == "kotoriminami" and thread["link"] not in seen_threads:
            seen_threads.add(thread["link"])
            await channel.send(f"📢 **New thread by kotoriminami!**\n**{thread['title']}**\n🔗 {thread['link']}\n<@{MENTION_ID}>")

# Start thread checking loop
@bot.event
async def on_ready():
    if not check_for_new_threads.is_running():
        check_for_new_threads.start()

# Slash command: scrapetest
@tree.command(name="scrapetest", description="Fetch a random thread")
async def scrapetest(interaction: discord.Interaction):
    threads = scrape_latest_threads()
    if not threads:
        await interaction.response.send_message("⚠️ No threads found.")
        return

    thread = random.choice(threads)
    await interaction.response.send_message(f"🎲 **Random Thread:** {thread['title']}\n🔗 {thread['link']}")

# Run bot
bot.run(TOKEN)
