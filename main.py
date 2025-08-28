import os
import discord
import random
import aiohttp
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

# 🔹 Store last seen threads
seen_threads = {
    "https://phcorner.org/threads/10pcs-netflix-ph-premium-autopay.2251640/",
    "https://phcorner.org/threads/netflix-ph.2250055/",
    "https://phcorner.org/threads/netflix-ph.2250052/",
    "https://phcorner.org/threads/netflix-ph-only-1.2250048/",
    "https://phcorner.org/threads/netflix-ph-ratrat.2249979/"
}


# ✅ Async helper: fetch HTML
async def fetch_html(url):
    async with aiohttp.ClientSession(cookies=COOKIES, headers=HEADERS) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


# ✅ Bot startup event
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

    if not check_for_new_threads.is_running():
       # check_for_new_threads.start()


# ✅ Scrape all threads (for /scrapetest)
async def scrape_all_threads():
    try:
        html = await fetch_html(FORUM_URL)
        soup = BeautifulSoup(html, "html.parser")
        threads = soup.select(".structItem-title a")

        return [
            {"title": t.get_text(strip=True), "link": "https://phcorner.org" + t["href"]}
            for t in threads
        ]
    except Exception as e:
        print(f"⚠️ Error scraping threads: {e}")
        return []


# ✅ Get latest thread by kotoriminami
async def get_latest_kotoriminami_thread():
    try:
        html = await fetch_html(FORUM_URL)
        soup = BeautifulSoup(html, "html.parser")
        threads = soup.select(".structItem-title a")

        for t in threads:
            title = t.get_text(strip=True)
            link = "https://phcorner.org" + t["href"]
            author = t.find_parent("div", class_="structItem").select_one(".username")
            if author and author.get_text(strip=True).lower() == "kotoriminami":
                if link not in seen_threads:
                    return {"title": title, "author": "kotoriminami", "link": link}
        return None
    except Exception as e:
        print(f"⚠️ Error scraping: {e}")
        return None


# ✅ Fetch last 5 threads by kotoriminami
async def fetch_last_5_threads():
    try:
        html = await fetch_html(SEARCH_URL)
        soup = BeautifulSoup(html, "html.parser")
        threads = soup.select(".structItem-title a")[:5]

        return "\n\n".join(
            [f"🔹 **{t.get_text(strip=True)}**\n🔗 https://phcorner.org{t['href']}" for t in threads]
        ) if threads else "⚠️ No recent threads found."
    except Exception as e:
        print(f"⚠️ Error fetching threads: {e}")
        return "⚠️ Error fetching latest threads."


# ✅ Loop to check new threads
@tasks.loop(seconds=5)
async def check_for_new_threads():
    latest_thread = await get_latest_kotoriminami_thread()
    if not latest_thread:
        return
    if latest_thread["link"] not in seen_threads:
        seen_threads.add(latest_thread["link"])
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(
                f"📢 **New thread by kotoriminami!**\n**{latest_thread['title']}**\n🔗 {latest_thread['link']}\n<@{MENTION_ID}>"
            )


# ✅ Slash commands
@tree.command(name="scrapetest", description="Fetch a random thread")
async def scrapetest(interaction: discord.Interaction):
    threads = await scrape_all_threads()
    if threads:
        thread = random.choice(threads)
        await interaction.response.send_message(
            f"🎲 **Random Thread:**\n**{thread['title']}**\n🔗 {thread['link']}"
        )
    else:
        await interaction.response.send_message("⚠️ No threads found.")


@tree.command(name="fetch", description="Fetch the 5 latest threads by kotoriminami")
async def fetch(interaction: discord.Interaction):
    latest_threads = await fetch_last_5_threads()
    await interaction.response.send_message(f"📜 **Latest 5 Threads by Kotoriminami:**\n\n{latest_threads}")


@tree.command(name="ping", description="Check if bot is online")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latency: `{latency}ms`")


# ✅ Run bot
bot.run(TOKEN)
