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
client = discord.Client(intents=intents)

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

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    await channel.send("✅ Bot is online and can send messages!")  # Test message
    check_for_new_posts.start()

@client.event
async def on_message(message):
    print(f"Received message: {message.content}")  # Debugging
    if message.author == client.user:
        return  # Ignore bot's own messages

    if message.content.lower() == "!test":
        await message.channel.send(f"✅ Test successful! {message.author.mention}")

# Run the bot
client.run(DISCORD_BOT_TOKEN)
