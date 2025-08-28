import os
import discord
import random
import requests
import logging
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from discord import app_commands

# 🔹 Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8", mode="a")
    ]
)
logger = logging.getLogger("discord_bot")

# 🔹 Load environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
MENTION_ID = int(os.getenv("DISCORD_USER_ID"))

# 🔹 Setup bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# 🔹 URLs & Cookies
FORUM_URL = "https://phcorner.org/forums/freemium-access.261/"
SEARCH_URL = "https://phcorner.org/search/member?user_id=2564330&content=thread"
COOKIES = {
    "xf_csrf": "S33fu4x-uzGaIhEU",
    "xf_session": "v9zviK3SpZIni1jr9cRpZRtcAWWkXTWy",
    "xf_user": "182831%2C4rFuvo33AFvwpIbyClrB-82ez24h5WJBONauWx3X"
}
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://phcorner.org/"
}

seen_threads = set()

# ✅ Bot ready
@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"⚠️ Error syncing commands: {e}")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"✅ Bot started! <@{MENTION_ID}>")
        logger.info("Startup message sent.")

    if not check_for_new_threads.is_running():
        check_for_new_threads.start()

    if not keep_active_ping.is_running():
        keep_active_ping.start()


# ✅ Scraping
def scrape_all_threads():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        res = session.get(FORUM_URL, cookies=COOKIES)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        return [{"title": t.get_text(strip=True), "link": "https://phcorner.org" + t["href"]} for t in soup.select(".structItem-title a")]
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        return []


def get_latest_kotoriminami_thread():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        res = session.get(FORUM_URL, cookies=COOKIES)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        for t in soup.select(".structItem-title a"):
            title, link = t.get_text(strip=True), "https://phcorner.org" + t["href"]
            author = t.find_parent("div", class_="structItem").select_one(".username")
            if author and author.get_text(strip=True).lower() == "kotoriminami":
                if link not in seen_threads:
                    return {"title": title, "link": link}
        return None
    except Exception as e:
        logger.error(f"Thread fetch error: {e}")
        return None


def fetch_last_5_threads():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        res = session.get(SEARCH_URL, cookies=COOKIES)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        return "\n\n".join([f"🔹 **{t.get_text(strip=True)}**\n🔗 https://phcorner.org{t['href']}" for t in soup.select(".structItem-title a")[:5]])
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return "⚠️ Error fetching threads."


# ✅ Background: check new threads
@tasks.loop(seconds=5)
async def check_for_new_threads():
    t = get_latest_kotoriminami_thread()
    if t and t["link"] not in seen_threads:
        seen_threads.add(t["link"])
        ch = bot.get_channel(CHANNEL_ID)
        if ch:
            await ch.send(f"📢 New thread by kotoriminami!\n**{t['title']}**\n🔗 {t['link']}\n<@{MENTION_ID}>")
            logger.info(f"Posted new thread: {t['title']}")


# ✅ Background: auto /ping every 20 days
@tasks.loop(hours=24*20)  # 20 days
async def keep_active_ping():
    ch = bot.get_channel(CHANNEL_ID)
    if ch:
        await ch.send("🔄 Auto `/ping` triggered to keep Active Developer Badge alive.")
        latency = round(bot.latency * 1000)
        await ch.send(f"🏓 Pong! Latency: `{latency}ms`")
        logger.info("Auto /ping executed.")


# ✅ Slash: /scrapetest
@tree.command(name="scrapetest", description="Fetch a random thread")
async def scrapetest(interaction: discord.Interaction):
    logger.info(f"/scrapetest by {interaction.user}")
    await interaction.response.defer()
    threads = scrape_all_threads()
    if threads:
        t = random.choice(threads)
        await interaction.followup.send(f"🎲 **Random Thread:**\n**{t['title']}**\n🔗 {t['link']}")
    else:
        await interaction.followup.send("⚠️ No threads found.")


# ✅ Slash: /fetch
@tree.command(name="fetch", description="Fetch 5 latest threads by kotoriminami")
async def fetch(interaction: discord.Interaction):
    logger.info(f"/fetch by {interaction.user}")
    await interaction.response.defer()
    await interaction.followup.send(f"📜 **Latest Threads:**\n\n{fetch_last_5_threads()}")


# ✅ Slash: /ping
@tree.command(name="ping", description="Check bot status")
async def ping(interaction: discord.Interaction):
    logger.info(f"/ping by {interaction.user}")
    await interaction.response.defer()
    latency = round(bot.latency * 1000)
    await interaction.followup.send(f"🏓 Pong! Latency: `{latency}ms`")


# ✅ Slash: /logs
@tree.command(name="logs", description="Show last 15 log lines")
async def logs(interaction: discord.Interaction):
    logger.info(f"/logs by {interaction.user}")
    await interaction.response.defer(ephemeral=True)
    try:
        with open("bot.log", "r", encoding="utf-8") as f:
            lines = f.readlines()[-15:]
        await interaction.followup.send("📜 **Logs:**\n```" + "".join(lines)[-1900:] + "```", ephemeral=True)
    except Exception as e:
        logger.error(f"Log read error: {e}")
        await interaction.followup.send("⚠️ Could not read logs.", ephemeral=True)


# ✅ Run
bot.run(TOKEN)
