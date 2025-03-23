import os
import time
import random
import requests
import discord
from bs4 import BeautifulSoup
from discord.ext import tasks, commands

# Environment Variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")  # Your Discord ID for mentions
URL = "https://phcorner.org/forums/freemium-access.261/"
USERNAME = "kotoriminami"

# Cookies (Replace with your actual session cookies)
COOKIES = {
    "xf_user": "182831%2C2anOgzI6W1479kHH2JYO6p2M7QJ-aILnSK3_Trw_",  # Your login cookie
    "xf_session": "uL4RdjjEq6uHOK85uvt0dLphjSUlgzop",
    "xf_csrf": "wRCpzH43hGS1IVmx"
}

# Headers (Simulates a real browser request)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Mobile Safari/537.36",
    "Referer": "https://phcorner.org/",
}

# Set up Discord bot
intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Track already notified posts
notified_posts = set()

import random

delay = random.randint(5, 15)  # Generate a random delay once
@tasks.loop(seconds=delay)
