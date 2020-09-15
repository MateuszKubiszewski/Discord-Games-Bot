import discord
import random
import jsonpickle
import re
from discord.ext import commands

import urllib

from ..S3 import write
from ..S3 import read

class Soldier:
    def __init__(self, erep_id: int, disc: str, name: str):
        self.erep_id = erep_id
        self.disc = disc
        self.name = name
        self.hits = 0
        self.xp_start = 0

class Zbiorki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.opened = False
        self.battle = ""
        self.soldiers = {}
        self.soldiers = jsonpickle.decode(read('soldiers.txt').Body, keys=True)

    @commands.command()
    @commands.has_role("Dowództwo")
    async def otworz(self, ctx, battle_link="A wtedy Jezus rzekł: Idźcie i nabijajcie expa.": str):
        """Prawidłowy sposób użycia: @otworz link\nlink - link do bitwy w eRepie [albo jakis komentarz zamiast linku] [opcjonalny argument].
        Pozwala żołnierzom używać komend join i finish.
        Jeśli użyjemy cudzysłowów, możemy do bitwy dodać jakiś komentarz, np. "link all div all in".
        Możemy też w cudzysłowiu dodać sam komentarz."""
        self.opened = True
        self.battle = battle_link
        await ctx.send("@everyone dołączamy i bijemy wedle wytycznych: " + battle_link)
    
    @otworz.error
    async def otworz_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send("```\nPrawidłowy sposób użycia:\n@otworz link\nlink - link do bitwy w eRepie [albo jakis komentarz zamiast linku]```")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")

    @commands.command()
    async def zarejestruj(self, ctx, id: int):
        """Prawidłowy sposób użycia: @zarejestruj id\nid - Twoje id w eRepublik [same cyferki, znajdziesz je na końcu linku do swojego profilu].
        Zapisuje użykownika wywołującego komendę do bazy żołnierzy."""
        author = ctx.message.author
        if author.id in self.soldiers:
            await ctx.send("Jesteś już zarejestrowany! Jeśli podałeś błędne ID i chcesz je zmienić, musisz się najpierw wyrejestrować \
                a następnie zarejestrować z nowym ID.")
        else:
            toAdd = Soldier(id, str(author), author.name)
            self.soldiers[author.id] = toAdd
            await ctx.send("Got it!")
            self.logsoldiers()
    
    @zarejestruj.error
    async def zarejestruj_error(self, ctx, error):
        await ctx.send("```\nPrawidłowy sposób użycia:\n@zarejestruj id\nid - Twoje id w eRepublik [same cyferki, znajdziesz je na końcu linku do swojego profilu]```")
    
    @commands.command()
    async def wyrejestruj(self, ctx):
        """Prawidłowy sposób użycia: @wyrejestruj id\nid - Twoje id w eRepublik [same cyferki, znajdziesz je na końcu linku do swojego profilu].
        Usuwa użykownika wywołującego komendę z bazy żołnierzy.
        UWAGA: użycie tej komendy spowoduje usunięcie zebranych hitów, jeśli jakieś są."""
        author = ctx.message.author
        if author.id not in self.soldiers:
            await ctx.send("Obawiam się, że i tak nie byłeś w bazie.")
        else:
            del self.soldiers[author.id]
            await ctx.send("Papuśki!")
            self.logsoldiers()

    @commands.command()
    async def join(self, ctx):
        """Prawidłowy sposób użycia: @join\nZapisuje stan punktów XP wywołującego komendę."""
        try:
            soldier = self.soldiers[ctx.message.author.id]
        except KeyError:
            await ctx.send("Musisz się najpierw zarejestrować!")
            return
        if self.opened:
            link = "https://www.erepublik.com/en/main/citizen-profile-json/" + str(soldier.erep_id)
            page = urllib.request.Request(link, headers = {'User-Agent': 'Mozilla/5.0'}) 
            content = urllib.request.urlopen(page).read()
            data = content.decode('ISO-8859-1')
            match = re.search("(\\\"experience_points\\\":[0-9]+)", data)
            soldier.xp_start = int(match.group(0)[20:])
            await ctx.send("Wyruszajmy zniszczyć naszych wrogów.")
            self.logsoldiers()
        else:
            await ctx.send("Brak otwartej zbiórki.")

    @commands.command()
    async def finish(self, ctx):
        """Prawidłowy sposób użycia: @finish\nNadpisuje stan punktów XP wywołującego komendę.
        Oblicza różnicę ze stanem XP podczas wywołania komendy @join i dodaje ją do ilości zebranych przez żołnierza hitów."""
        try:
            soldier = self.soldiers[ctx.message.author.id]
        except KeyError:
            await ctx.send("Musisz się najpierw zarejestrować!")
            return
        if self.opened and soldier.xp_start > 0:           
            link = "https://www.erepublik.com/en/main/citizen-profile-json/" + str(soldier.erep_id)
            page = urllib.request.Request(link, headers = {'User-Agent': 'Mozilla/5.0'}) 
            content = urllib.request.urlopen(page).read()
            data = content.decode('ISO-8859-1')
            match = re.search("(\\\"experience_points\\\":[0-9]+)", data)
            finish_exp = int(match.group(0)[20:])
            toAdd = finish_exp - soldier.xp_start
            soldier.hits += toAdd
            soldier.xp_start = finish_exp
            await ctx.send(f"Ilość dopisanych hitów: {toAdd}.")
            self.logsoldiers()
        else:
            await ctx.send("Albo nie ma otwartej zbiórki, albo nie dołączyłeś do niej. W każdym wypadku Twoje polecenie jest nieprawidłowe. Wiesz ile ja tuszu marnuje na zapisywanie takich wygibasów?!")

    @commands.command()
    async def daj_link(self, ctx):
        """Prawidłowy sposób użycia: @daj_link\nWysyła link do bitwy w której trzeba bić."""
        if self.opened:
            await ctx.send(self.battle)
        else:
            await ctx.send("Brak otwartej zbiórki.")
    
    @commands.command()
    @commands.has_role("Dowództwo")
    async def zamknij(self, ctx):
        """Prawidłowy sposób użycia: @zamknij\nZabiera możliwość używania komend @join i @finish.
        Zeruje zapisany poziom XP żołnierzy [hity zostają w bazie]. Jeśli ktoś zapomniał użyć @finish to ucina zrobione na zbiórce hitki :(."""
        self.opened = False
        self.battle = ""
        for item in list(self.soldiers.values()):
            item.xp_start = 0
        await ctx.send("Dziękujemy za udział w zbiórce!")
        self.logsoldiers()
    
    @zamknij.error
    async def zamknij_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")
    
    @commands.command()
    @commands.has_role("Dowództwo")
    async def rozlicz(self, ctx):
        """Prawidłowy sposób użycia: @rozlicz\nZeruje ilość hitów wszystkich żołnierzy - komenda do użycia po np. wydaniu należnego CC."""
        for item in list(self.soldiers.values()):
            item.hits = 0
        await ctx.send("Done.")
        self.logsoldiers()
    
    @rozlicz.error
    async def rozlicz_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")

    @commands.command()
    @commands.has_role("Dowództwo")
    async def statystyki(self, ctx):
        """Prawidłowy sposób użycia: @statystyki\nWyświetla żołnierzy w bazie, ich zebrane hity i linki do profilów."""
        toSend = "```\nName: Hits - Link\n"
        for k, v in self.soldiers.items():
            toSend += f"{v.name}: {v.hits} - https://www.erepublik.com/en/citizen/profile/{v.erep_id}\n"
        toSend += "```"
        await ctx.send(toSend)
    
    @statystyki.error
    async def statystyki_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")

    @commands.command()
    @commands.has_role("Dowództwo")
    async def edit(self, ctx, soldier: discord.Member, n: int):
        """Prawidłowy sposób użycia: @edit @nick hity
        @nick - slap tego, któremu chcemy wyeditować hity, bez wzmianki nie zadziała.
        hity - liczba hitów do dodania. Jeśli chcemy usunąć można wpisać na minusie.
        @edit @Donald 10 - dodaje 10 hitów.
        @edit @Donald -10 - zabiera 10 hitów."""
        self.soldiers[soldier.id].hits += n
        await ctx.send("Done.")
        self.logsoldiers()
    
    @edit.error
    async def edit_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")
    
    @commands.command()
    async def help_zolnierz(self, ctx):
        """Prawidłowy sposób użycia: @help_zolnierz
        Wysyła link do miniporadnika wyjaśniającego jak brać udział w zbiórkach."""
        await ctx.send("https://i.imgur.com/nrBU0NI.png")
    
    @commands.command()
    @commands.has_role("Dowództwo")
    async def help_dowodca(self, ctx):
        """Prawidłowy sposób użycia: @help_dowodca
        Wysyła link do miniporadnika wyjaśniającego komendy dla Dowództwa."""
        await ctx.send("https://i.imgur.com/rhccXFt.png")
    
    @help_dowodca.error
    async def help_dowodca_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")
    
    @commands.command()
    @commands.has_role("Dowództwo")
    async def zapisz(self, ctx):
        """Prawidłowy sposób użycia: @zapisz
        Zapisuje obecnych w bazie żołnierzy na trwałym pliku."""
        write('soldiers.txt', jsonpickle.encode(self.soldiers, keys=True, indent=4))

    def logsoldiers(self):
        print(jsonpickle.encode(self.soldiers, keys=True, indent=4))