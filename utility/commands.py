from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import json
import random
import urllib.request

from amazons3 import S3
from . import resources as res 
# https://stackoverflow.com/questions/58906183/vs-code-python-interpreter-cant-find-my-venv
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
        soup = self.get_soup_from_link_with_guard("http://piszsuchary.pl/losuj")
        joke = soup.find("div", {"class": "kot_na_suchara"}).find("img")['alt']
        await ctx.send(f"```\n{joke}```")
    
    @commands.command()
    async def bash(self, ctx):
        soup = self.get_soup_from_link_with_guard("http://bash.org.pl/random/")
        strips = soup.find("div", {"class": "quote post-content post-body"}).stripped_strings
        joke = '\n'.join(strip for strip in strips)
        await ctx.send(f"```\n{joke}```")
    
    @commands.command()
    async def ciekawostka(self, ctx):
        await ctx.send(self.drukuj_ciekawostke(random.randint(0, len(res.Ciekawostki) - 1)))
    
    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(515983210455236646)
        await channel.send(self.drukuj_ciekawostke(random.randint(0, len(res.Ciekawostki) - 1)))
    
    def logsoldiers(self):
        S3.write('punkty.txt', json.dumps(self.soldiers))
        print(json.dumps(self.punktyTGS))

    def drukuj_ciekawostke(self, number):
        return "```\n" + res.Ciekawostki[number] + "```"

    def get_soup_from_link_with_guard(self, link: str) -> BeautifulSoup:
        soup = None
        while not soup:
            soup = self.get_soup_from_link(link)
        return soup

    def get_soup_from_link(self, link: str) -> BeautifulSoup:
        page = urllib.request.Request(link, headers = {'User-Agent': 'Mozilla/5.0'})
        content = urllib.request.urlopen(page).read()
        data = content.decode('UTF-8')
        return BeautifulSoup(data, 'html.parser')

