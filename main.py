import asyncio
import discord
from discord.ext import commands

# # heroku run - currently will not be used
# import os
# TOKEN = os.environ["DISCORD_TOKEN"]

# local run
from dotenv import load_dotenv # type: ignore
import os
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="@", intents=intents)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

async def load():
    await bot.load_extension("familiada.commands")
    await bot.load_extension("spying.commands")
    await bot.load_extension("stats.commands")
    await bot.load_extension("utility.commands")
    await bot.load_extension("zbiorki.commands")

async def main():
    await load()
    await bot.start(TOKEN)

asyncio.run(main())