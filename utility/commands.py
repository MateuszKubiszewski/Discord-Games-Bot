import discord
import random
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.punktyTGS = {}
   
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dodaj_punkt(self, ctx, gracze: commands.Greedy[discord.Member]):
        for member in new_members:
            if member not in self.punktyTGS:
                self.punktyTGS[member] = 1
            else:
                self.punktyTGS[member] += 1
        print(self.punktyTGS)
    
    @commands.command()
    async def ranking_graczy(self, ctx):
        sorted_members = sorted(self.punktyTGS.items(), key=lambda x: x[1], reverse=True)
        toSend = "'''\nRanking:\n"
        for index, member in enumerate(sorted_members, start=0):
            toSend += f"{index + 1}. {member[0].display_name}: {member[1]}\n"
        await ctx.send(toSend)
