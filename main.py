import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

from familiada import commands as comms 
# from hangman import hangman as hang

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix="@")
bot.add_cog(comms.Familiada(bot))
bot.add_cog(hang.Hangman(bot))

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.run(TOKEN)