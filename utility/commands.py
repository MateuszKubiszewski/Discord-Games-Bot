import discord
import random
import json
from discord.ext import commands

import urllib.request
import re

from amazons3 import S3

from . import resources as res 

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.punktyTGS = {}
        response = S3.read('punkty.txt')
        self.punktyTGS = json.loads(response['Body'].read().decode('utf-8'))
        random.seed()
   
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
        print(message)
        print(message.content)
    
    @commands.command()
    async def suchar(self, ctx):
        link = "http://www.kinyen.pl/dowcipy/losowy/"
        page = urllib.request.Request(link, headers = {'User-Agent': 'Mozilla/5.0'}) 
        content = urllib.request.urlopen(page).read()
        data = content.decode('UTF-8')
        match = re.search("(<div class=\\\"joke\\\">)\n.+\n.+", data)
        string = match.group(0)[21:-9]
        striing = string.replace("<br />", "\n")
        striiing = striing.replace("&quot;", "\"")
        joke = "```\n" + striiing + "```"
        await ctx.send(joke)
    
    @commands.command()
    async def ciekawostka(self, ctx):
        drukuj_ciekawostke(random.randint(0, len(res.Ciekawostki) - 1))
    
    @commands.Cog.listener()
    async def on_ready(self):
        drukuj_ciekawostke(random.randint(0, len(res.Ciekawostki) - 1))
    
    def logsoldiers(self):
        S3.write('punkty.txt', json.dumps(self.soldiers))
        print(json.dumps(self.punktyTGS))

    async def drukuj_ciekawostke(self, number):
        await ctx.send("```\n" + res.Ciekawostki[number] + "```")

