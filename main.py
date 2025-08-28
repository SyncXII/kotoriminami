import os
import discord
import random
import requests
import logging
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from discord import app_commands

# ==============================
# 🔹 Logging Setup
# ==============================
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

# ==============================
# 🔹 Load environment variables
# ==============================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
MENTION_ID = int(os.getenv("DISCORD_USER_ID"))

# ==============================
# 🔹 Discord Bot Setup
# ==============================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Slash command handler

# ==============================
# 🔹 URLs
# ==============================
FORUM_URL = "https://phcorner.org/forums/freemium-access.261/"
SEARCH_URL = "https://phcorner.org/search/member?user_id=2564330&content=thread"

# 🔹 Cookies for Authentication
COOKIES = {
    "xf_csrf": "S33fu4x-uzGaIhEU",
    "xf_session": "v9zviK3SpZIni1jr9cRpZRtcAWWkXTWy",
    "xf_user": "182831%2C4rFuvo33AFvwpIbyClrB-82ez24h5WJBONauWx3X"
}

# 🔹 Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://phcorner.org/"
}

# 🔹 Store seen threads
seen_threads = set()


# ==============================
# ✅ Bot Events
# ==============================
@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user}")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"⚠️ Error syncing commands: {e}")

    # Notify channel
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"✅ Bot started! <@{MENTION_ID}>")

    # Start tasks
    if not check_for_new_threads.is_running():
        check_for_new_threads.start()
    if not keep_active.is_running():
        keep_active.start()


# ==============================
# ✅ Scraping Functions
# ==============================
def scrape_all_threads():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(FORUM_URL, cookies=COOKIES)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        threads = soup.select(".structItem-title a")

        return [{"title": t.get_text(strip=True), "link": "https://phcorner.org" + t["href"]} for t in threads]
    except Exception as e:
        logger.error(f"⚠️ Error scraping threads: {e}")
        return []


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

            author = thread.find_parent("div", class_="structItem").select_one(".username")
            if author and author.get_text(strip=True).lower() == "kotoriminami":
                if link not in seen_threads:
                    return {"title": title, "link": link}
        return None
    except Exception as e:
        logger.error(f"⚠️ Error scraping: {e}")
        return None


def fetch_last_5_threads():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(SEARCH_URL, cookies=COOKIES)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        threads = soup.select(".structItem-title a")[:5]

        return "\n\n".join([f"🔹 **{t.get_text(strip=True)}**\n🔗 https://phcorner.org{t['href']}" for t in threads]) or "⚠️ No threads found."
    except Exception as e:
        logger.error(f"⚠️ Error fetching threads: {e}")
        return "⚠️ Error fetching latest threads."


# ==============================
# ✅ Background Tasks
# ==============================
@tasks.loop(seconds=5)
async def check_for_new_threads():
    latest = get_latest_kotoriminami_thread()
    if latest and latest["link"] not in seen_threads:
        seen_threads.add(latest["link"])
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"📢 **New thread by kotoriminami!**\n**{latest['title']}**\n🔗 {latest['link']}\n<@{MENTION_ID}>")


# 🔹 Keeps bot active every ~25 days
@tasks.loop(hours=600)
async def keep_active():
    logger.info("Running keep_active task (/ping)...")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🔄 Keep-alive ping! Bot is still active.")


# ==============================
# ✅ Slash Commands
# ==============================
@tree.command(name="scrapetest", description="Fetch a random thread")
async def scrapetest(interaction: discord.Interaction):
    logger.info(f"/scrapetest used by {interaction.user}")
    threads = scrape_all_threads()
    if threads:
        t = random.choice(threads)
        await interaction.response.send_message(f"🎲 **Random Thread:**\n**{t['title']}**\n🔗 {t['link']}")
    else:
        await interaction.response.send_message("⚠️ No threads found.")


@tree.command(name="fetch", description="Fetch the 5 latest threads by kotoriminami")
async def fetch(interaction: discord.Interaction):
    logger.info(f"/fetch used by {interaction.user}")
    await interaction.response.send_message(f"📜 **Latest 5 Threads by Kotoriminami:**\n\n{fetch_last_5_threads()}")


@tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    logger.info(f"/ping used by {interaction.user}")
    await interaction.response.send_message(f"🏓 Pong! Latency: `{round(bot.latency * 1000)}ms`")


@tree.command(name="logs", description="Show the last 20 log lines")
async def logs(interaction: discord.Interaction):
    logger.info(f"/logs used by {interaction.user}")

    # Restrict logs to owner only
    if interaction.user.id != MENTION_ID:
        await interaction.response.send_message("⛔ You are not allowed to view logs.", ephemeral=True)
        return

    try:
        with open("bot.log", "r", encoding="utf-8") as f:
            lines = f.readlines()[-20:]
        log_output = "".join(lines)
        if len(log_output) > 1900:
            log_output = log_output[-1900:]
        await interaction.response.send_message(f"📜 **Last 20 Logs:**\n```{log_output}```")
    except FileNotFoundError:
        await interaction.response.send_message("⚠️ No log file found yet.")
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Error reading logs: {e}")


# ==============================
# ✅ Run Bot
# ==============================
bot.run(TOKEN)
