import os
import time
import random
import requests
import discord
from bs4 import BeautifulSoup
from discord.ext import tasks

# Environment Variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
URL = "https://phcorner.org/new-topics/"
USERNAME = "kotoriminami"

# Set up Discord client
intents = discord.Intents.default()
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=intents)

# Track already notified posts
notified_posts = set()

@tasks.loop(seconds=random.randint(5, 15))  # Randomized delay between 5-15 seconds
async def check_for_new_posts():
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    posts = soup.find_all("div", class_="structItem-title")  # Find all new topics

    for post in posts:
        author_div = post.find_next_sibling("div")  # Check the username
        if author_div:
            author_tag = author_div.find("a", class_="username")
            if author_tag and author_tag.text.strip() == USERNAME:
                title = post.text.strip()
                link = "https://phcorner.org" + post.find("a")["href"]  # Get full link to the post

                if link not in notified_posts:
                    channel = client.get_channel(DISCORD_CHANNEL_ID)
                    await channel.send(f"📢 **New Post by {USERNAME}**:\n🔗 **{title}**\n➡️ {link}")
                    notified_posts.add(link)

    # Change the loop delay dynamically
    check_for_new_posts.change_interval(seconds=random.randint(5, 15))

@bot.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    await channel.send("✅ Bot is online and can send messages!")  # Test message
    check_for_new_posts.start()

@bot.command()
async def test(ctx):
    await ctx.send(f"✅ Test successful! {ctx.author.mention}")
    
# Run the bot
bot.run(DISCORD_BOT_TOKEN)
