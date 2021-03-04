import json
from discord.ext import commands
import math
from typing import List, Dict, TypedDict
import urllib.request

from amazons3 import S3
from .additionalIds import additionalIds
from .airRanks import airRanks
from .groundRanks import groundRanks
from .medals import medalsAndScale
from .medals import index

class MedalData(TypedDict):
    name: str
    count: int

class SoldierData(TypedDict):
    id: str
    name: str
    expLevel: int
    strength: int
    medals: List[MedalData]
    groundRank: int
    airRank: int

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muLink = 'https://www.erepublik.com/en/military/military-unit-data/?groupId=177&panel=members'
        self.citizenDataLink = 'https://www.erepublik.com/en/main/citizen-profile-json/'
        self.citizenProfileLink = 'https://www.erepublik.com/en/citizen/profile/'
        self.soldiersData: Dict[str, SoldierData] = {}
        self.newMembers: List[str] = []
        self.messages: List[str] = []

    @commands.Cog.listener()
    async def on_ready(self):
        self.GoThroughSoldiersData()
        channel = self.bot.get_channel(811664465829036052)
        for message in self.messages:
            await channel.send(message)
        if len(self.messages) == 0:
            await channel.send("```\nNothing special this time.```")

    def GoThroughSoldiersData(self) -> None:
        soldiersData = self.ReadSoldiersDataFromDatabase()
        currentSoldiersData = self.ReadCurrentSoldiersData()
        for ID in currentSoldiersData.keys():
            if str(ID) in soldiersData:
                oldData: SoldierData = soldiersData[str(ID)]
                currentData: SoldierData = currentSoldiersData[str(ID)]
                name = oldData["name"]
                link = self.citizenProfileLink + str(ID)
                self.AppendExpLevelMessage(name, link, oldData["expLevel"], currentData["expLevel"])
                self.AppendStrengthMessage(name, link, oldData["strength"], currentData["strength"])
                self.AppendMedalsMessage(name, link, oldData["medals"], currentData["medals"])
                self.AppendGroundRankMessage(name, link, oldData["groundRank"], currentData["groundRank"])
                self.AppendAirRankMessage(name, link, oldData["airRank"], currentData["airRank"])
            else:
                self.newMembers.append(str(ID))
        for member in self.newMembers:
            self.messages.append(f"```\nA new player has joined TGS!\nProfile link: {self.citizenProfileLink}{member}.```")
        self.SaveSoldiersData(currentSoldiersData)

    def ReadSoldiersDataFromDatabase(self) -> Dict[int, SoldierData]:
        response = S3.read('stats.txt')
        return json.loads(response['Body'].read().decode('utf-8'))

    def ReadCurrentSoldiersData(self) -> Dict[int, SoldierData]:
        militaryUnitData = self.GET(self.muLink)
        membersID: List[int] = militaryUnitData["panelContents"]["membersList"]
        # adding members from aTGS
        membersID.extend(additionalIds)
        soldiersData: Dict[str, SoldierData] = {}
        for ID in membersID:
            citizenData = self.GET(self.citizenDataLink + str(ID))
            soldierData: SoldierData = {
                'id': str(ID),
                'name': citizenData["citizen"]["name"],
                'expLevel': citizenData["citizen"]["level"],
                'strength': citizenData["military"]["militaryData"]["strength"],
                'medals': [],
                'groundRank': citizenData["military"]["militaryData"]["rankNumber"],
                'airRank': citizenData["military"]["militaryData"]["aircraft"]["rankNumber"]
            }
            for medal in medalsAndScale:
                soldierData["medals"].append(MedalData(
                    name = medal,
                    count = citizenData["achievements"][index[medal]]["count"]
                ))
            soldiersData[str(ID)] = soldierData
        return soldiersData

    def SaveSoldiersData(self, data: Dict[int, SoldierData]) -> None:
        S3.write('stats.txt', json.dumps(data))
   
    def GET(self, link: str) -> Dict:
        page = urllib.request.Request(link, headers = {'User-Agent': 'Mozilla/5.0'}) 
        content = urllib.request.urlopen(page).read()
        data = content.decode('ISO-8859-1')
        return json.loads(data)
    
    def AppendExpLevelMessage(self, soldierName: str, profileLink: str, oldExpLevel: int, currentExpLevel: int) -> None:
        if oldExpLevel < currentExpLevel:
            newLevelsRange: range[int] = range(oldExpLevel + 1, currentExpLevel + 1)
            smallExpRules = [
                currentExpLevel < 90,
                any(x in [30, 50, 70] for x in newLevelsRange)
            ]
            bigExpRules = [
                currentExpLevel > 90,
                any(x % 100 == 0 for x in newLevelsRange)
            ]
            if all(smallExpRules) or all(bigExpRules):
                levelToPrint = round(currentExpLevel, -1)
                self.messages.append(f"```\n{soldierName} reached level {levelToPrint}.\nProfile link: {profileLink}.```")
    
    def AppendStrengthMessage(self, soldierName: str, profileLink: str, oldStrength: int, currentStrength: int) -> None:
        if oldStrength < currentStrength:
            smallStrengthRules = [
                currentStrength < 30000,
                oldStrength % 25000 > currentStrength % 25000
            ]
            bigStrengthRules = [
                currentStrength > 30000,
                oldStrength % 50000 > currentStrength % 50000
            ]
            if all(bigStrengthRules) or all(smallStrengthRules):
                strengthToPrint = int(round(currentStrength, -3))
                self.messages.append(f"```\n{soldierName} reached {strengthToPrint} strength.\nProfile link: {profileLink}.```")
    
    def AppendMedalsMessage(self, soldierName: str, profileLink: str, oldMedalData: List[MedalData], currentMedalData: List[MedalData]) -> None:
        for oldData, currentData in zip(oldMedalData, currentMedalData):
            if oldData["count"] < currentData["count"]:
                newMedalsRange: range[int] = range(oldData["count"] + 1, currentData["count"] + 1)
                for x in newMedalsRange:
                    if x % medalsAndScale[oldData["name"]] == 0:
                        self.messages.append(f"```\n{soldierName} reached {x} {oldData['name']} medals.\nProfile link: {profileLink}.```")
    
    def AppendGroundRankMessage(self, soldierName: str, profileLink: str, oldGroundRank: int, currentGroundRank: int) -> None:
        if currentGroundRank > oldGroundRank:
            if currentGroundRank > 65 or currentGroundRank == 62:
                for i in range(oldGroundRank + 1, currentGroundRank + 1):
                    self.messages.append(f"```\n{soldierName} reached {groundRanks[i]}.```")
                self.messages.append(f"```\nProfile link: {profileLink}.```")

    def AppendAirRankMessage(self, soldierName: str, profileLink: str, oldAirRank: int, currentAirRank: int) -> None:
        if currentAirRank > oldAirRank:
            if currentAirRank > 43 and currentAirRank in [26, 32, 38, 39]:
                for i in range(oldAirRank + 1, currentAirRank + 1):
                    self.messages.append(f"```\n{soldierName} reached {airRanks[i]}.```")
                self.messages.append(f"```\nProfile link: {profileLink}.```")