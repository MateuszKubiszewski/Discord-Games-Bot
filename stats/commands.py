from botocore.exceptions import PaginationError
from discord import File as discordFile
from discord.ext import commands
from io import BytesIO
import json
from PIL import Image, ImageDraw, ImageFont
from secrets import randbelow
from sys import exc_info
from typing import List, Dict, TypedDict
import urllib.request

from amazons3 import S3
from .additionalIds import additionalCitizenIds, militaryUnitIds
from .airRanks import airRanks
from .groundRanks import groundRanks
from .notifyingData import englishPlayers, femalePlayers, NotificationType, soldiersToNotifyDiscordIds
from .medals import medalsAndScale, airMedals, groundMedals, otherMedals, index

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
        self.imageMessages: List[str] = []

    def muDataLink(self, muId: str) -> str:
        return f'https://www.erepublik.com/en/military/military-unit-data/?groupId={muId}&panel=members'

    @commands.Cog.listener()
    async def on_ready(self):
        self.GoThroughSoldiersData()
        # old text messages
        channel = self.bot.get_channel(811664465829036052)
        for message in self.messages:
            await channel.send(message)
        if len(self.messages) == 0:
            await channel.send("```\nNobody to congratulate this time.```")
        # new image messages [WIP]
        channel_beta = self.bot.get_channel(881189575052116028)
        for imageMessage in self.imageMessages:
            self.PrepareImage(imageMessage)
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
                self.imageMessages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.EXP, levelToPrint))
    
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
                self.imageMessages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.STRENGTH, strengthToPrint))
    
    def AppendMedalsMessage(self, soldierName: str, profileLink: str, oldMedalData: List[MedalData], currentMedalData: List[MedalData]) -> None:
        for medalName, medalScale in medalsAndScale.items():
            scale = medalScale
            if soldierName == "Tomko." and medalName == "Battle Hero" or medalName == "True Patriot":
                scale = 1000
            oldMedal = next((medal for medal in oldMedalData if medal["name"] == medalName), None)
            currentMedal = next((medal for medal in currentMedalData if medal["name"] == medalName), None)
            if oldMedal and currentMedal and oldMedal["count"] < currentMedal["count"]:
                medalsRange: range[int] = range(oldMedal["count"] + 1, currentMedal["count"] + 1)
                for x in medalsRange:
                    if x % scale == 0:
                        self.messages.append(f"```\n{soldierName} reached {x} {medalName} medals.\nProfile link: {profileLink}.```")
                        if len(self.imageMessages) > 0:
                            lastMessage = self.imageMessages[-1]
                            if soldierName in lastMessage and medalName in lastMessage:
                                self.imageMessages.remove(lastMessage)
                        self.imageMessages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.MEDAL,
                            newNumberMilestone=x, newTextMilestone=medalName))

    def AppendGroundRankMessage(self, soldierName: str, profileLink: str, oldGroundRank: int, currentGroundRank: int) -> None:
        if currentGroundRank > oldGroundRank:
            if currentGroundRank > 65 or currentGroundRank == 62:
                for i in range(oldGroundRank + 1, currentGroundRank + 1):
                    self.messages.append(f"```\n{soldierName} reached {groundRanks[i]}.```")
                self.messages.append(f"```\nProfile link: {profileLink}.```")
                self.imageMessages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.RANK, newTextMilestone=groundRanks[currentGroundRank]))

    def AppendAirRankMessage(self, soldierName: str, profileLink: str, oldAirRank: int, currentAirRank: int) -> None:
        if currentAirRank > oldAirRank:
            if currentAirRank > 43 or currentAirRank in [26, 32, 38, 39]:
                for i in range(oldAirRank + 1, currentAirRank + 1):
                    self.messages.append(f"```\n{soldierName} reached {airRanks[i]}.```")
                self.messages.append(f"```\nProfile link: {profileLink}.```")
                self.imageMessages.append(self.GetMessageToPrintOnImage(soldierName, NotificationType.RANK, newTextMilestone=airRanks[currentAirRank]))

    def PrepareImage(self, message: str) -> None:
        imageFromS3 = S3.readImage(self.GetImagePath(message))
        img = Image.open(BytesIO(imageFromS3))
        editable_img = ImageDraw.Draw(img)
        image_width = img.width
        image_height = img.height
        
        font = S3.readFont("fonts/DejaVuSans.ttf")
        myFont = ImageFont.truetype(font, 40)
        w, h = myFont.getsize(message)
        w2, h2 = myFont.getsize("Gratulacje!")
        if w > image_width - 200:
            myFont = ImageFont.truetype(font, 30)
            w, h = myFont.getsize(message)
            w2, h2 = myFont.getsize("Gratulacje!")

        editable_img.text(((image_width - w) / 2, image_height - 96), message, fill="white", font=myFont)
        editable_img.text(((image_width - w2) / 2, image_height - 50), "Gratulacje!", fill="white", font=myFont)
        img.save("result.png", "PNG")
    
    def GetImagePath(self, message: str) -> str:
        GROUND_IMAGES_AMOUNT = 24
        AIR_IMAGES_AMOUNT = 9
        PATRIOT_IMAGES_AMOUNT = 4
        OTHER_IMAGES_AMOUNT = 7
        # Air Image Condition
        if any(airRank in message for airRank in airRanks.values()) or any(airMedal in message for airMedal in airMedals):
            imageIndex = randbelow(AIR_IMAGES_AMOUNT) + 1
            return f"images/air/{imageIndex}.png"
        # Ground Image Condition
        elif any(groundRank in message for groundRank in groundRanks.values()) or any(groundMedal in message for groundMedal in groundMedals):
            imageIndex = randbelow(GROUND_IMAGES_AMOUNT) + 1
            return f"images/tank/{imageIndex}.png"
        # Patriot Image Condition
        elif "True Patriot" in message:
            imageIndex = randbelow(PATRIOT_IMAGES_AMOUNT) + 1
            return f"images/TP/{imageIndex}.png"
        else:
            imageIndex = randbelow(OTHER_IMAGES_AMOUNT) + 1
            return f"images/inne/{imageIndex}.png"
    
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
            message += f"{newNumberMilestone} {newTextMilestone} medals!"
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
            if newNumberMilestone == 1:
                message += f"{newNumberMilestone} medal {newTextMilestone}!"
            elif newNumberMilestone in [2, 3, 4]:
                message += f"{newNumberMilestone} medale {newTextMilestone}!"
            else:
                message += f"{newNumberMilestone} medali {newTextMilestone}!"
        else:
            message += f"rangę {newTextMilestone}!"
        return message