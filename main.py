import os
import discord
import random
import asyncio
import requests
from bs4 import BeautifulSoup
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

# ✅ Updated Cookies for Authentication
COOKIES = {
    "xf_csrf": "wRCpzH43hGS1IVmx",
    "xf_session": "uL4RdjjEq6uHOK85uvt0dLphjSUlgzop",
    "xf_user": "182831%2C2anOgzI6W1479kHH2JYO6p2M7QJ-aILnSK3_Trw_"
}

# Headers to prevent bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://phcorner.org/"
}

# Store last seen thread
last_seen_thread = None


# ✅ Mention user when the bot starts
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"⚠️ Error syncing commands: {e}")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"✅ Bot started! <@{MENTION_ID}>")


# ✅ Scrape only the **latest** thread posted by kotoriminami
def get_latest_kotoriminami_thread():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(FORUM_URL, cookies=COOKIES)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        threads = soup.select(".structItem-title a")

        for thread in threads:
            title = thread.get_text(strip=True)
            link = "https://phcorner.org" + thread["href"]

            # Check if author is "kotoriminami"
            author_element = thread.find_parent("div", class_="structItem").select_one(".username")
            if author_element and author_element.get_text(strip=True).lower() == "kotoriminami":
                return {"title": title, "author": "kotoriminami", "link": link}

        return None  # No thread found
    except Exception as e:
        print(f"⚠️ Error scraping: {e}")
        return None


# ✅ Task to check for new threads every 5 seconds
@tasks.loop(seconds=5)
async def check_for_new_threads():
    global last_seen_thread

    latest_thread = get_latest_kotoriminami_thread()
    if not latest_thread:
        return

    if last_seen_thread is None or last_seen_thread["link"] != latest_thread["link"]:
        last_seen_thread = latest_thread
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"📢 **New thread by kotoriminami!**\n**{latest_thread['title']}**\n🔗 {latest_thread['link']}\n<@{MENTION_ID}>")


# ✅ Start
