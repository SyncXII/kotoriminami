import os
import discord
import random
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from discord import app_commands

# 🔹 Load environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
MENTION_ID = int(os.getenv("DISCORD_USER_ID"))

# 🔹 Set up bot with commands and intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Slash commands handler

# 🔹 Forum URL (Change if needed)
FORUM_URL = "https://phcorner.org/forums/freemium-access.261/"

# 🔹 Cookies for Authentication (Ensure they're valid)
COOKIES = {
    "xf_csrf": "wRCpzH43hGS1IVmx",
    "xf_session": "uL4RdjjEq6uHOK85uvt0dLphjSUlgzop",
    "xf_user": "182831%2C2anOgzI6W1479kHH2JYO6p2M7QJ-aILnSK3_Trw_"
}

# 🔹 Headers to prevent bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://phcorner.org/"
}

# 🔹 Store last seen threads to avoid duplicate notifications
seen_threads = {
    "https://phcorner.org/threads/10pcs-netflix-ph-premium-autopay.2251640/",
    "https://phcorner.org/threads/netflix-ph.2250055/",
    "https://phcorner.org/threads/netflix-ph.2250052/",
    "https://phcorner.org/threads/netflix-ph-only-1.2250048/",
    "https://phcorner.org/threads/netflix-ph-ratrat.2249979/"
}


# ✅ Bot startup event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"⚠️ Error syncing commands: {e}")

    # Mention user on startup
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"✅ Bot started! <@{MENTION_ID}>")

    # Start the thread-checking loop
    if not check_for_new_threads.is_running():
        check_for_new_threads.start()


# ✅ Scrape all threads (For `/scrapetest` and `!scrapetest`)
def scrape_all_threads():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(FORUM_URL, cookies=COOKIES)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        threads = soup.select(".structItem-title a")

        thread_list = []
        for thread in threads:
            title = thread.get_text(strip=True)
            link = "https://phcorner.org" + thread["href"]
            thread_list.append({"title": title, "link": link})

        return thread_list
    except Exception as e:
        print(f"⚠️ Error scraping threads: {e}")
        return []


# ✅ Get the latest thread by `kotoriminami`
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
                if link not in seen_threads:
                    return {"title": title, "author": "kotoriminami", "link": link}

        return None  # No new thread found
    except Exception as e:
        print(f"⚠️ Error scraping: {e}")
        return None


# ✅ Check for new threads every 5 seconds
@tasks.loop(seconds=5)
async def check_for_new_threads():
    latest_thread = get_latest_kotoriminami_thread()
    if not latest_thread:
        return

    if latest_thread["link"] not in seen_threads:
        seen_threads.add(latest_thread["link"])
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"📢 **New thread by kotoriminami!**\n**{latest_thread['title']}**\n🔗 {latest_thread['link']}\n<@{MENTION_ID}>")


# ✅ Slash command: `/scrapetest` (Fetch a random thread)
@tree.command(name="scrapetest", description="Fetch a random thread")
async def scrapetest(interaction: discord.Interaction):
    threads = scrape_all_threads()

    if threads:
        thread = random.choice(threads)
        await interaction.response.send_message(f"🎲 **Random Thread:**\n**{thread['title']}**\n🔗 {thread['link']}")
    else:
        await interaction.response.send_message("⚠️ No threads found.")


# ✅ Prefix command: `!scrapetest` (For testing if slash command fails)
@bot.command()
async def scrapetest(ctx):
    threads = scrape_all_threads()

    if threads:
        thread = random.choice(threads)
        await ctx.send(f"🎲 **Random Thread:**\n**{thread['title']}**\n🔗 {thread['link']}")
    else:
        await ctx.send("⚠️ No threads found.")


# ✅ Prefix command: `!ping` (Check if bot is online)
@bot.command()
async def test(ctx):
    latency = round(bot.latency * 1000)  # Convert to ms
    await ctx.send(f"🏓 Pong! Bot is online. Latency: `{latency}ms`")


# ✅ Run the bot
bot.run(TOKEN)
