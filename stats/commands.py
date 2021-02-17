import json
from discord.ext import commands
from typing import List, Dict, TypedDict

import urllib.request

from amazons3 import S3
from . import airRanks as ar
from . import groundRanks as gr

class SoldierData(TypedDict):
    name: str
    profileLink: str
    expLevel: int
    rhMedals: int
    ssMedals: int
    groundRank: int
    airRank: int

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muLink = 'https://www.erepublik.com/en/military/military-unit-data/?groupId=177&panel=members'
        self.citizenLink = 'https://www.erepublik.com/en/main/citizen-profile-json/'
        self.soldiersData: Dict[int, SoldierData] = {}
        self.messages: List[str] = []

    @commands.Cog.listener()
    async def on_ready(self):
        self.GoThroughSoldiersData()
        channel = self.bot.get_channel(811664465829036052)
        for message in self.messages:
            await channel.send(message)

    def GoThroughSoldiersData(self) -> None:
        soldiersData = self.ReadSoldiersDataFromDatabase()
        currentSoldiersData = self.ReadCurrentSoldiersData()
        for ID in currentSoldiersData.keys():
            oldData: SoldierData = soldiersData[ID]
            currentData: SoldierData = currentSoldiersData[ID]
            name = oldData["name"]
            link = oldData["profileLink"]
            self.AppendExpLevelMessage(name, link, oldData["expLevel"], currentData["expLevel"])
            self.AppendRhMedalsMessage(name, link, oldData["rhMedals"], currentData["rhMedals"])
            self.AppendSsMedalsMessage(name, link, oldData["ssMedals"], currentData["ssMedals"])
            self.AppendGroundRankMessage(name, link, oldData["groundRank"], currentData["groundRank"])
            self.AppendAirRankMessage(name, link, oldData["airRank"], currentData["airRank"])
        self.SaveSoldiersData(currentSoldiersData)

    def ReadSoldiersDataFromDatabase(self) -> Dict[int, SoldierData]:
        response = S3.read('stats.txt')
        return json.loads(response['Body'].read().decode('utf-8'))

    def ReadCurrentSoldiersData(self) -> Dict[int, SoldierData]:
        militaryUnitData = self.GET()
        membersID: List[int] = militaryUnitData["panelContents"]["membersList"]
        soldiersData: Dict[int, SoldierData] = {}
        for ID in membersID:
            profileLink = self.citizenLink + str(ID)
            citizenData = self.GET(profileLink)
            soldierData: SoldierData = {
                'name': citizenData["citizen"]["name"],
                'profileLink': profileLink,
                'expLevel': citizenData["citizen"]["level"],
                'rhMedals': citizenData["achievements"][0]["count"],
                'ssMedals': citizenData["achievements"][9]["count"],
                'groundRank': citizenData["military"]["militaryData"]["rankNumber"],
                'airRank': citizenData["military"]["militaryData"]["aircraft"]["rankNumber"]
            }
            soldiersData[ID] = soldierData
        return soldiersData

    def SaveSoldiersData(self, data: Dict[int, SoldierData]) -> None:
        S3.write('stats.txt', json.dumps(data))
   
    def GET(link: str) -> Dict:
        page = urllib.request.Request(link, headers = {'User-Agent': 'Mozilla/5.0'}) 
        content = urllib.request.urlopen(page).read()
        data = content.decode('ISO-8859-1')
        return json.loads(data)
    
    def AppendExpLevelMessage(self, soldierName: str, profileLink: str, oldExpLevel: int, currentExpLevel: int) -> None:
        if currentExpLevel > oldExpLevel:
            self.messages.append(f"```\n{soldierName} reached level {currentExpLevel}.\nProfile link: {profileLink}.```")
            #if currentExpLevel % 50 == 0:
                #self.messages.append(f"```\n{soldierName} reached level {currentExpLevel}.\nProfile link: {profileLink}.```")
    
    def AppendRhMedalsMessage(self, soldierName: str, profileLink: str, oldRhMedals: int, currentRhMedals: int) -> None:
        if currentRhMedals > oldRhMedals:
            self.messages.append(f"```\n{soldierName} reached {currentRhMedals} RH medals.\nProfile link: {profileLink}.```")
            #if currentRhMedals % 50 == 0:
                #self.messages.append(f"```\n{soldierName} reached {currentRhMedals} RH medals.\nProfile link: {profileLink}.```")
    
    def AppendSsMedalsMessage(self, soldierName: str, profileLink: str, oldSsMedals: int, currentSsMedals: int) -> None:
        if currentSsMedals > oldSsMedals:
            self.messages.append(f"```\n{soldierName} reached {currentSsMedals * 250} strength.\nProfile link: {profileLink}.```")
            #if currentSsMedals % 200 == 0:
                #self.messages.append(f"```\n{soldierName} reached {currentSsMedals * 250} strength.\nProfile link: {profileLink}.```")
    
    def AppendGroundRankMessage(self, soldierName: str, profileLink: str, oldGroundRank: int, currentGroundRank: int) -> None:
        if currentGroundRank > oldGroundRank:
            for i in range(oldGroundRank + 1, currentGroundRank + 1):
                self.messages.append(f"```\n{soldierName} reached {gr.GroundRanks[i]}.```")
            self.messages.append(f"```\nProfile link: {profileLink}.```")
                

    def AppendAirRankMessage(self, soldierName: str, profileLink: str, oldAirRank: int, currentAirRank: int) -> None:
        if currentAirRank > oldAirRank:
            for i in range(oldAirRank + 1, currentAirRank + 1):
                self.messages.append(f"```\n{soldierName} reached {ar.AirRanks[i]}.```")
            self.messages.append(f"```\nProfile link: {profileLink}.```")