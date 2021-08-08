import json
from discord.ext import commands
from typing import List, Dict
import urllib.request

from amazons3 import S3
from .resources import militaryUnitIds

class Spying(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.soldiersData: Dict[str, List[str]] = {}
        self.messages: List[str] = []

    def muDataLink(self, muId: str) -> str:
        return f'https://www.erepublik.com/en/military/military-unit-data/?groupId={muId}&panel=members'

    @commands.Cog.listener()
    async def on_ready(self):
        self.GoThroughSoldiersIds()
        channel = self.bot.get_channel(811664465829036052)
        for message in self.messages:
            await channel.send(message)
        if len(self.messages) == 0:
            await channel.send("```\nNothing special this time.```")

    def GoThroughSoldiersIds(self) -> None:
        oldSoldiersIds = self.ReadSoldiersIdsFromDatabase()
        currentSoldiersIds = {
            "PCA": [],
            "GROM": [],
            "PMTF": [],
            "LP": []
        }
        for MU in currentSoldiersIds.keys():
            oldIds = oldSoldiersIds[MU]
            currentIds = self.ReadCurrentSoldiersIds(MU)
            for currentId in currentIds:
                if currentId not in oldIds:
                    self.messages.append(f'```\nA new player has joined {MU}! Profile link: https://www.erepublik.com/en/citizen/profile/{currentId}```')
            currentSoldiersIds[MU] = currentIds
        self.SaveSoldiersIds(currentSoldiersIds)

    def ReadCurrentSoldiersIds(self, MU: str) -> List[str]:
        page = urllib.request.Request(self.muDataLink(militaryUnitIds[MU]), headers = {'User-Agent': 'Mozilla/5.0'}) 
        content = urllib.request.urlopen(page).read()
        data = content.decode('ISO-8859-1')
        militaryUnitDataDictionary = json.loads(data)
        return militaryUnitDataDictionary["panelContents"]["membersList"]

    def ReadSoldiersIdsFromDatabase(self) -> Dict[str, List[str]]:
        response = S3.read('spying-ids.txt')
        return json.loads(response['Body'].read().decode('utf-8'))

    def SaveSoldiersIds(self, ids: Dict[str, List[str]]) -> None:
        S3.write('spying-ids.txt', json.dumps(ids))