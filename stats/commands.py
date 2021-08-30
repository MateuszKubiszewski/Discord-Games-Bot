from discord import File as discordFile
from discord.ext import commands
from io import BytesIO
import json
from PIL import Image, ImageDraw, ImageFont
from secrets import randbelow
from typing import List, Dict, TypedDict
import urllib.request

from amazons3 import S3
from .additionalIds import additionalCitizenIds
from .additionalIds import militaryUnitIds
from .airRanks import airRanks
from .groundRanks import groundRanks
from .notifyingData import englishPlayers
from .notifyingData import femalePlayers
from .notifyingData import NotificationType
from .notifyingData import soldiersToNotifyDiscordIds
from .medals import medalsAndScale
from .medals import index

class ImageData(TypedDict):
    player: str
    newNumberMilestone: int
    newTextMilestone: str
    notificationType: NotificationType

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
        self.citizenDataLink = 'https://www.erepublik.com/en/main/citizen-profile-json/'
        self.citizenProfileLink = 'https://www.erepublik.com/en/citizen/profile/'
        self.soldiersData: Dict[str, SoldierData] = {}
        self.newMembersIds: List[str] = []
        self.messages: List[str] = []
        self.new_messages: List[str] = []

    def muDataLink(self, muId: str) -> str:
        return f'https://www.erepublik.com/en/military/military-unit-data/?groupId={muId}&panel=members'

    @commands.Cog.listener()
    async def on_ready(self):
        self.GoThroughSoldiersData()
        # old messages
        channel = self.bot.get_channel(811664465829036052)
        for message in self.messages:
            await channel.send(message)
        if len(self.messages) == 0:
            await channel.send("```\nNothing special this time.```")
        # new messages [WIP]
        channel_beta = self.bot.get_channel(881189575052116028)
        for new_message in self.new_messages:
            self.PrepareImage(new_message)
            await channel_beta.send(file=discordFile("result.png"))

    def GoThroughSoldiersData(self) -> None:
        oldSoldiersData = self.ReadSoldiersDataFromDatabase()
        currentSoldiersData = self.ReadCurrentSoldiersData()
        for ID in currentSoldiersData.keys():
            if str(ID) in oldSoldiersData:
                oldData: SoldierData = oldSoldiersData[str(ID)]
                currentData: SoldierData = currentSoldiersData[str(ID)]
                name = oldData["name"]
                link = self.citizenProfileLink + str(ID)
                self.AppendExpLevelMessage(name, link, oldData["expLevel"], currentData["expLevel"])
                self.AppendStrengthMessage(name, link, oldData["strength"], currentData["strength"])
                self.AppendMedalsMessage(name, link, oldData["medals"], currentData["medals"])
                self.AppendGroundRankMessage(name, link, oldData["groundRank"], currentData["groundRank"])
                self.AppendAirRankMessage(name, link, oldData["airRank"], currentData["airRank"])
            else:
                self.newMembersIds.append(str(ID))
        for member in self.newMembersIds:
            self.messages.append(f"```\nA new player has joined TGS or TGS Academy!\nProfile link: {self.citizenProfileLink}{member}.```")
        for ID in oldSoldiersData:
            if ID not in currentSoldiersData:
                self.messages.append(f"```\nA player has left TGS or TGS Academy!\nProfile link: {self.citizenProfileLink}{ID}.```")
        self.SaveSoldiersData(currentSoldiersData)

    def ReadSoldiersDataFromDatabase(self) -> Dict[int, SoldierData]:
        response = S3.read('stats.txt')
        return json.loads(response['Body'].read().decode('utf-8'))

    def ReadCurrentSoldiersData(self) -> Dict[int, SoldierData]:
        TgsData = self.GetDataDictionaryFromPage(self.muDataLink(militaryUnitIds["TGS"]))
        TgsAcademyData = self.GetDataDictionaryFromPage(self.muDataLink(militaryUnitIds["ATGS"]))
        membersIDs: List[int] = TgsData["panelContents"]["membersList"] + TgsAcademyData["panelContents"]["membersList"]
        # adding some friendly profiles which are neither in TGS nor in ATGS
        membersIDs += additionalCitizenIds
        soldiersData: Dict[str, SoldierData] = {}
        for ID in membersIDs:
            citizenData = self.GetDataDictionaryFromPage(self.citizenDataLink + str(ID))
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
   
    def GetDataDictionaryFromPage(self, page: str) -> Dict:
        page = urllib.request.Request(page, headers = {'User-Agent': 'Mozilla/5.0'}) 
        content = urllib.request.urlopen(page).read()
        data = content.decode('ISO-8859-1')
        return json.loads(data)
    
    def AppendExpLevelMessage(self, soldierName: str, profileLink: str, oldExpLevel: int, currentExpLevel: int) -> None:
        if oldExpLevel < currentExpLevel:
            newLevelsRange: range[int] = range(oldExpLevel + 1, currentExpLevel + 1)
            smallExpRules = [
                currentExpLevel < 90,
                any(x in [35, 50, 70] for x in newLevelsRange)
            ]
            bigExpRules = [
                currentExpLevel > 90,
                any(x % 100 == 0 for x in newLevelsRange)
            ]
            if all(smallExpRules) or all(bigExpRules):
                levelToPrint = round(currentExpLevel, -1)
                if currentExpLevel < 50:
                    levelToPrint = 35
                self.messages.append(f"```\n{soldierName} reached level {levelToPrint}.\nProfile link: {profileLink}.```")
                self.new_messages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.EXP, levelToPrint))
    
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
                self.new_messages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.STRENGTH, strengthToPrint))
    
    def AppendMedalsMessage(self, soldierName: str, profileLink: str, oldMedalData: List[MedalData], currentMedalData: List[MedalData]) -> None:
        # should be adjusted so it takes data from dictionary not one by one
        for oldData, currentData in zip(oldMedalData, currentMedalData):
            medalName = oldData["name"]
            scale = medalsAndScale[medalName]
            if soldierName == "Tomko." and medalName == "Battle Hero" or medalName == "True Patriot":
                scale = 1000
            if oldData["count"] < currentData["count"]:
                newMedalsRange: range[int] = range(oldData["count"] + 1, currentData["count"] + 1)
                for x in newMedalsRange:
                    if x % scale == 0:
                        self.messages.append(f"```\n{soldierName} reached {x} {medalName} medals.\nProfile link: {profileLink}.```")
                        if len(self.new_messages) > 0:
                            last_message = self.new_messages[-1]
                            if soldierName in last_message and medalName in last_message:
                                self.new_messages.remove(last_message)
                        self.new_messages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.MEDAL,
                            newNumberMilestone=x, newTextMilestone=medalName))

    def AppendGroundRankMessage(self, soldierName: str, profileLink: str, oldGroundRank: int, currentGroundRank: int) -> None:
        if currentGroundRank > oldGroundRank:
            if currentGroundRank > 65 or currentGroundRank == 62:
                for i in range(oldGroundRank + 1, currentGroundRank + 1):
                    self.messages.append(f"```\n{soldierName} reached {groundRanks[i]}.```")
                self.messages.append(f"```\nProfile link: {profileLink}.```")
                self.new_messages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.RANK, newTextMilestone=groundRanks[currentGroundRank]))

    def AppendAirRankMessage(self, soldierName: str, profileLink: str, oldAirRank: int, currentAirRank: int) -> None:
        if currentAirRank > oldAirRank:
            if currentAirRank > 43 or currentAirRank in [26, 32, 38, 39]:
                for i in range(oldAirRank + 1, currentAirRank + 1):
                    self.messages.append(f"```\n{soldierName} reached {airRanks[i]}.```")
                self.messages.append(f"```\nProfile link: {profileLink}.```")
                self.new_messages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.RANK, newTextMilestone=groundRanks[currentAirRank]))

    def PrepareImage(self, message: str) -> None:
        imageIndex = randbelow(45) + 1
        imageFromS3 = S3.readImage(f"images/{imageIndex}.png")
        img = Image.open(BytesIO(imageFromS3))
        editable_img = ImageDraw.Draw(img)
        image_width = img.width
        image_height = img.height
        
        font = S3.readFont("fonts/DejaVuSans.ttf")
        myFont = ImageFont.truetype(font, 40)
        w, h = myFont.getsize(message)
        w2, h2 = myFont.getsize("Gratulacje!")
        if w > image_width:
            myFont = ImageFont.truetype(font, 35)
            w, h = myFont.getsize(message)
            w2, h2 = myFont.getsize("Gratulacje!")

        editable_img.text(((image_width - w) / 2, image_height - 96), message, fill="white", font=myFont)
        editable_img.text(((image_width - w2) / 2, image_height - 50), "Gratulacje!", fill="white", font=myFont)
        img.save("result.png", "PNG")
    
    def GetMessageToPrintOnImage(self, player: str, notificationType: NotificationType, newNumberMilestone: int = 0, newTextMilestone: str = "") -> str:
        if player in englishPlayers:
            return self.GetEnglishMessage(player, notificationType, newNumberMilestone, newTextMilestone)
        else:
            return self.GetPolishMessage(player, notificationType, newNumberMilestone, newTextMilestone)

    def GetEnglishMessage(self, player: str, notificationType: NotificationType, newNumberMilestone: int = 0, newTextMilestone: str = "") -> str:
        # XY reached level XX!
        # XY reached XX strength!
        # XY reached XX YY medals!
        # XY reached YY!
        message = player + " reached "
        if notificationType == NotificationType.EXP:
            message += f"level {newNumberMilestone}!"
        elif notificationType == NotificationType.STRENGTH:
            message += f"{newNumberMilestone} strength!"
        elif notificationType == NotificationType.MEDAL:
            message == f"{newNumberMilestone} {newTextMilestone} medals!"
        else:
            message += f"{newTextMilestone}!"
        return message

    def GetPolishMessage(self, player: str, notificationType: NotificationType, newNumberMilestone: int = 0, newTextMilestone: str = "") -> str:
        # XY zdobył/a XX poziom!
        # XY zdobył/a XX punktów siły!
        # XY zdobył/a XX medali YY!
        # XY zdobył/a rangę YY!
        verb = " zdobyła " if player in femalePlayers else " zdobył "
        message = player + verb
        if notificationType == NotificationType.EXP:
            message += f"{newNumberMilestone} poziom!"
        elif notificationType == NotificationType.STRENGTH:
            message += f"{newNumberMilestone} punktów siły!"
        elif notificationType == NotificationType.MEDAL:
            message == f"{newNumberMilestone} medali {newTextMilestone}!"
        else:
            message += f"rangę {newTextMilestone}!"
        return message