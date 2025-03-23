import os
import discord
import random
import asyncio
import requests
from bs4 import BeautifulSoup  # Added for better thread extraction
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

# ✅ Updated Cookies (Use valid session cookies)
COOKIES = {
    "xf_csrf": "wRCpzH43hGS1IVmx",
    "xf_session": "uL4RdjjEq6uHOK85uvt0dLphjSUlgzop",
    "xf_user": "182831%2C2anOgzI6W1479kHH2JYO6p2M7QJ-aILnSK3_Trw_"
}

# Headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://phcorner.org/"
}

# Store seen threads to avoid duplicate notifications
seen_threads = set()

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

# ✅ Scrape latest threads from the forum
def scrape_latest_threads():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(FORUM_URL, cookies=COOKIES)
        response.raise_for_status()
        
        # ✅ Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        threads = []
        
        for thread in soup.select(".structItem-title a"):
            title = thread.get_text(strip=True)
            link = "https://phcorner.org" + thread["href"]
            author = "Unknown"

            # Find the corresponding author
            author_element = thread.find_parent("div", class_="structItem").select_one(".username")
            if author_element:
                author = author_element.get_text(strip=True)

            threads.append({"title": title, "author": author, "link": link})

        return threads
    except Exception as e:
        print(f"⚠️ Error scraping: {e}")
        return []

# ✅ Task to check for new threads every 5 seconds
@tasks.loop(seconds=5)
async def check_for_new_threads():
    threads = scrape_latest_threads()
    if not threads:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    for thread in threads:
        if thread["author"].lower() == "kotoriminami" and thread["link"] not in seen_threads:
            seen_threads.add(thread["link"])
            await channel.send(f"📢 **New thread by kotoriminami!**\n**{thread['title']}**\n🔗 {thread['link']}\n<@{MENTION_ID}>")

# ✅ Start checking for new threads after bot is ready
@bot.event
async def on_ready():
    if not check_for_new_threads.is_running():
        check_for_new_threads.start()

# ✅ Slash command: /scrapetest (Fetch a random thread)
@tree.command(name="scrapetest", description="Fetch a random thread")
async def scrapetest(interaction: discord.Interaction):
    threads = scrape_latest_threads()
    if not threads:
        await interaction.response.send_message("⚠️ No threads found.")
        return

    thread = random.choice(threads)
    await interaction.response.send_message(f"🎲 **Random Thread:** {thread['title']}\n🔗 {thread['link']}")

# ✅ Run bot
bot.run(TOKEN)
