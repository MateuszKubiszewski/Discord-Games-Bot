from discord.ext import commands

# importing cogs
from familiada import commands as comms
from spying import commands as spying_comms
from stats import commands as s_comms 
from utility import commands as u_comms
from zbiorki import commands as z_comms
# from hangman import hangman as hang

# # local run
# from dotenv import load_dotenv # type: ignore
# import os
# load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')

# heroku run
import os
TOKEN = os.environ["DISCORD_TOKEN"]

bot = commands.Bot(command_prefix="@")
bot.add_cog(comms.Familiada(bot))
bot.add_cog(spying_comms.Spying(bot))
bot.add_cog(s_comms.Stats(bot))
bot.add_cog(u_comms.Utility(bot))
bot.add_cog(z_comms.Zbiorki(bot))
# bot.add_cog(hang.Hangman(bot))

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.run(TOKEN)