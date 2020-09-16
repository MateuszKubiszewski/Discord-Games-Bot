import discord
import random
import json
import jsonpickle
from discord.ext import commands

from amazons3 import S3

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.punktyTGS = {}
        # with open('punkty.txt', 'r') as file:
        #     self.punktyTGS = json.loads(file.read())
        response = S3.read('punkty.txt')
        self.punktyTGS = jsonpickle.decode(response['Body'].read().decode('utf-8'), keys=True)
   
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def dodaj_punkt(self, ctx, new_members: commands.Greedy[discord.Member]):
        for member in new_members:
            toadd = str(member)
            if toadd not in self.punktyTGS:
                self.punktyTGS[toadd] = 1
            else:
                self.punktyTGS[toadd] += 1
        logs = ""
        for k, v in self.punktyTGS.items():
            logs += f"{k}: {v}    "
        # with open('punkty.txt', 'w') as file:
        #     file.write(json.dumps(self.punktyTGS))
        self.logsoldiers()
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def zabierz_punkt(self, ctx, new_members: commands.Greedy[discord.Member]):
        for member in new_members:
            toadd = str(member)
            if toadd not in self.punktyTGS:
                continue
            else:
                self.punktyTGS[toadd] -= 1
        logs = ""
        for k, v in self.punktyTGS.items():
            logs += f"{k}: {v}    "
        # with open('punkty.txt', 'w') as file:
        #     file.write(json.dumps(self.punktyTGS))
        self.logsoldiers()
    
    @commands.command()
    async def ranking_graczy(self, ctx):
        sorted_members = sorted(self.punktyTGS.items(), key=lambda x: x[1], reverse=True)
        toSend = "```\nRanking:\n"
        for index, member in enumerate(sorted_members, start=0):
            toSend += f"{index + 1}. {member[0]}: {member[1]}\n"
        toSend += "```"
        await ctx.send(toSend)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def test(self, ctx):
        message = await self.bot.wait_for('message')
        # await ctx.send("@everyone")
        print(message)
        print(message.content)
    
    def logsoldiers(self):
        S3.write('punkty.txt', jsonpickle.encode(self.soldiers, keys=True, indent=4))
        print(json.dumps(self.punktyTGS))
