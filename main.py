import os
import random
import discord
import asyncio
import aiohttp
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

# Load environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
MENTION_ID = os.getenv("DISCORD_USER_ID")

# Forum URL to scrape
FORUM_URL = "https://phcorner.org/forums/freemium-access.261/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
COOKIES = {
    "xf_csrf": "wRCpzH43hGS1IVmx",
    "xf_session": "uL4RdjjEq6uHOK85uvt0dLphjSUlgzop",
    "xf_user": "182831%2C2anOgzI6W1479kHH2JYO6p2M7QJ-aILnSK3_Trw_"
}

# Discord bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Store last seen thread to prevent duplicate notifications
last_seen_thread = None

async def scrape_forum():
    """Scrapes the forum for the latest threads."""
    async with aiohttp.ClientSession() as session:
        async with session.get(FORUM_URL, headers=HEADERS, cookies=COOKIES) as response:
            if response.status != 200:
                print(f"Failed to fetch forum data, status: {response.status}")
                return None

            soup = BeautifulSoup(await response.text(), "html.parser")
            threads = soup.find_all("div", class_="structItem--thread")

            if not threads:
                print("No threads found.")
                return None

            new_threads = []
            for thread in threads:
                user = thread.find("a", class_="username")
                if user and user.text.strip() == "kotoriminami":
                    title_tag = thread.find("a", class_="structItem-title")
                    if title_tag:
                        thread_title = title_tag.text.strip()
                        thread_link = "https://phcorner.org" + title_tag["href"]
                        new_threads.append((thread_title, thread_link))

            return new_threads

@tasks.loop(seconds=5)
async def check_for_new_threads():
    """Checks for new threads by 'kotoriminami' and notifies in Discord."""
    global last_seen_thread
    new_threads = await scrape_forum()

    if new_threads:
        for title, link in new_threads:
            if last_seen_thread != link:
                last_seen_thread = link
                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    await channel.send(f"📢 **New Thread by kotoriminami!**\n{title}\n🔗 {link}\n<@{MENTION_ID}>")
                else:
                    print("Channel not found.")

@bot.command()
async def scrapetest(ctx):
    """Fetches a random thread from any user and sends it to Discord."""
    async with aiohttp.ClientSession() as session:
        async with session.get(FORUM_URL, headers=HEADERS, cookies=COOKIES) as response:
            if response.status != 200:
                await ctx.send("Failed to fetch forum data.")
                return

            soup = BeautifulSoup(await response.text(), "html.parser")
            threads = soup.find_all("div", class_="structItem--thread")

            if not threads:
                await ctx.send("No threads found.")
                return

            random_thread = random.choice(threads)
            title_tag = random_thread.find("a", class_="structItem-title")

            if title_tag:
                thread_title = title_tag.text.strip()
                thread_link = "https://phcorner.org" + title_tag["href"]
                await ctx.send(f"🎲 **Random Thread:**\n{thread_title}\n🔗 {thread_link}")

@bot.event
async def on_ready():
    """Starts the thread-checking loop when the bot is ready."""
    print(f"Logged in as {bot.user}")
    check_for_new_threads.start()

bot.run(TOKEN)
