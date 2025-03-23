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

# 🔹 Set up bot with intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Slash commands handler

# 🔹 URLs
FORUM_URL = "https://phcorner.org/forums/freemium-access.261/"
SEARCH_URL = "https://phcorner.org/search/member?user_id=2564330&content=thread"  # Fetch threads from user

# 🔹 Cookies for Authentication
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
seen_threads = set()


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


# ✅ Fetch latest 5 threads by `kotoriminami`
def fetch_latest_threads():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(SEARCH_URL, cookies=COOKIES)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        threads = soup.select(".structItem")[:5]  # Get latest 5 thread elements

        thread_list = []
        for thread in threads:
            title_element = thread.select_one(".structItem-title a")
            if title_element:
                title = title_element.get_text(strip=True)
                link = "https://phcorner.org" + title_element["href"]
                thread_list.append(f"🔹 **{title}**\n🔗 {link}")

        return "\n\n".join(thread_list) if thread_list else "⚠️ No recent threads found."
    except Exception as e:
        print(f"⚠️ Error fetching threads: {e}")
        return "⚠️ Error fetching latest threads."


# ✅ Check for new threads every 5 seconds
@tasks.loop(seconds=5)
async def check_for_new_threads():
    latest_threads = fetch_latest_threads()
    if not latest_threads:
        return

    latest_thread = latest_threads.split("\n\n")[0]  # Get the first/latest thread
    thread_link = latest_thread.split("\n")[1].replace("🔗 ", "").strip()

    if thread_link not in seen_threads:
        seen_threads.add(thread_link)
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"📢 **New thread by kotoriminami!**\n{latest_thread}\n<@{MENTION_ID}>")


# ✅ Slash command: `/fetch` (Fetch last 5 threads by `kotoriminami`)
@tree.command(name="fetch", description="Fetch the 5 latest threads by kotoriminami")
async def fetch(interaction: discord.Interaction):
    latest_threads = fetch_latest_threads()
    await interaction.response.send_message(f"📜 **Latest 5 Threads by Kotoriminami:**\n\n{latest_threads}")


# ✅ Slash command: `/ping` (Check if bot is online)
@tree.command(name="ping", description="Check if the bot is online and responsive")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)  # Convert to ms
    await interaction.response.send_message(f"🏓 Pong! Bot is online. Latency: `{latency}ms`")


# ✅ Run the bot
bot.run(TOKEN)
