import os
import discord
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
RECENT_CONTENT_URL = "https://phcorner.org/members/kotoriminami.2564330/#recent-content"

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

# ✅ Fetch last 5 recent content (Threads, Replies, Posts)
def fetch_recent_content():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(RECENT_CONTENT_URL, cookies=COOKIES)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content_items = soup.select(".contentRow-main")[:5]  # Get the 5 latest entries

        content_list = []
        for item in content_items:
            title_element = item.select_one(".contentRow-title a")
            link = "https://phcorner.org" + title_element["href"]
            title = title_element.get_text(strip=True)

            # Get content type (Thread, Post, or Reply)
            content_type = "Thread" if "thread" in link else "Reply" if "post" in link else "Post"

            # Get message preview
            message_preview = item.select_one(".contentRow-snippet")
            preview_text = message_preview.get_text(strip=True) if message_preview else "No preview available."

            content_list.append(f"🔹 **[{content_type}] {title}**\n📢 *\"{preview_text}\"*\n🔗 {link}")

        return "\n\n".join(content_list) if content_list else "⚠️ No recent content found."
    except Exception as e:
        print(f"⚠️ Error fetching content: {e}")
        return "⚠️ Error fetching recent content."

# ✅ Slash command: `/fetch` (Fetch the latest 5 posts by Kotoriminami)
@tree.command(name="fetch", description="Fetch the 5 latest posts by Kotoriminami (threads, replies, or posts)")
async def fetch(interaction: discord.Interaction):
    latest_content = fetch_recent_content()
    await interaction.response.send_message(f"📜 **Latest 5 Recent Posts by Kotoriminami:**\n\n{latest_content}")

# ✅ Slash command: `/ping` (Check if bot is online)
@tree.command(name="ping", description="Check if the bot is online and responsive")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)  # Convert to ms
    await interaction.response.send_message(f"🏓 Pong! Bot is online. Latency: `{latency}ms`")

# ✅ Run the bot
bot.run(TOKEN)
