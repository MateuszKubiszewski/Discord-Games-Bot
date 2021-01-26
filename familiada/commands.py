import discord
import random
import json
from discord.ext import commands

from . import resources as res
from . import classes as cl

class Familiada(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.teams = []
        self.participants = []
        self.questions = []
        for questions, answers, points in zip(res.Questions, res.Answers, res.Points):
            toAppend = cl.Question(questions, answers, points)
            self.questions.append(toAppend)
        self.asked_questions = [] # cos z tym trzeba zrobic
        # moze tablica z asked questions dla kazdego serwera, event handler na dolaczenie do serweru ktory dodaje serwer do listy?
        # with open('asked-questions.txt', 'r') as file:
        #     self.asked_questions = json.load(file)
        self.used_colors = []
        self.current_question = -1
        print(self.asked_questions)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def familiada(self, ctx):
        tosend = "```\nNa początek krótki dowcip\n"
        random.seed()
        number = random.randint(0, len(res.Puns) - 1)
        tosend += f"{res.Puns[number]}\nUdział w dzisiejszej grze biorą:\n```"
        for team in self.teams:
            tosend += f"{team}"
        await ctx.send(tosend)

    @familiada.error
    async def familiada_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def zbierz_druzyne(self, ctx, members: commands.Greedy[discord.Member]):
        if len(self.used_colors) == len(res.Colors):
            await ctx.send("Niestety skończyło mi się miejsce na nowe drużyny :c.")
            return
        number = random.randint(0, len(res.Colors) - 1)
        while number in self.used_colors:
            number = random.randint(0, len(res.Questions) - 1)
        membs = {}
        for member in members:
            self.participants.append(member)
            membs[member] = 0
        toappend = cl.Team(res.Colors[number], membs)
        self.teams.append(toappend)
        self.used_colors.append(number)
        await ctx.send(toappend)

    @zbierz_druzyne.error
    async def zbierz_druzyne_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send("```\nPrawidłowy sposób użycia:\n@zbierz_druzyne slap\nslap - oznaczenie kogos na discordzie, np @Donald \
                \nMożna oznaczyć kilku graczy, wtedy wywołujemy każdy nick kolejno oddzielając slapy je spacją.```")
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")

    @commands.command()
    async def druzyny(self, ctx):
        if len(self.teams) == 0:
            return
        ret = ""
        for team in self.teams:
            ret += f"{team}"
        await ctx.send(ret)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pytanie(self, ctx): 
        # pick the question and send it
        if len(self.asked_questions) == len(self.questions):
            # number = random.randint(0, len(self.questions) - 1)
            await ctx.send('Wyczerpały mi się pytania :<<<.')
            return
        else:
            number = random.randint(0, len(self.questions) - 1)
            while number in self.asked_questions:
                number = random.randint(0, len(self.questions) - 1)
        question = self.questions[number]
        self.current_question = number
        self.asked_questions.append(number)
        await ctx.send(question)
        # now wait for the answers
        self.current_answers = []
        n = len(self.asked_questions)
        while len(self.current_answers) < len(question.answers):
            # check if a new question was asked, if it was, then return
            if n != len(self.asked_questions):
                return
            score = 0
            # collecting answers until proper answer is sent
            guess = await self.bot.wait_for('message')
            if guess.author not in self.participants:
                continue
            guess_content = guess.content.lower()
            if guess_content not in question.answers or guess_content in self.current_answers:
                continue
            # finding the amount of points for the answer
            for index, answer in enumerate(question.answers, start = 0):
                if answer == guess_content:
                    score = question.points[index]
                    # add the guess to the answered list
                    self.current_answers.append(answer) 
            # finding the team to which the points should be added - and adding them
            for team in self.teams:
                if guess.author in team.members:
                    team.members[guess.author] += score
                    team.points += score
            #something to send after an aswer has been guessed
            await ctx.send(f"```\nDobra odpowiedź {guess.author.display_name}! {score} punktów za {guess_content}.```")
        #something to send after all answers have been guessed
        await ctx.send("```\nWszystkie odpowiedzi zostały odgadnięte!```")
        await self.print_question(ctx, self.current_question)
        self.current_question = -1

    @pytanie.error
    async def pytanie_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def podsumowanie(self, ctx):
        if len(self.teams) == 0:
            await ctx.send("'''\nZapraszam do stworzenia nowej gry.'''")
            return
        winner = self.teams[0]
        for team in self.teams:
            if team.points > winner.points:
                winner = team
        tosend = f"```\nZWYCIĘZCĄ DZISIEJSZEGO DNIA ZOSTAJE ZESPÓŁ {winner.name}!!!\nPodsumowanie:\n```"
        for team in self.teams:
            tosend += f"{team}"
        await ctx.send(tosend)
        self.ordnung_muss_sein()
        print(self.asked_questions)
        # with open('asked-questions.txt', 'w') as file:
        #     json.dump(self.asked_questions, file)
    
    @podsumowanie.error
    async def podsumowanie_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("```\nBrak uprawnień do użycia tej komendy.```")

    @commands.command()
    async def punkty(self, ctx):
        if self.current_question == -1:
            return
        await self.print_question(ctx, self.current_question)
    
    @commands.command()
    async def familiada_pomoc(self, ctx):
        await ctx.send("https://i.imgur.com/oJC4RQR.png")
    
    def ordnung_muss_sein(self):
        self.participants.clear()
        self.teams.clear()
        self.used_colors.clear()

    async def print_question(self, ctx, question: int):
        question = self.questions[question]
        ret = f"```\n{question.content}\n"
        for index, answer in enumerate(question.answers, start = 0):
            if answer in self.current_answers:
                ret += f"{index + 1}. {question.answers[index]}: {question.points[index]} \n"
            else:
                ret += f"{index + 1}. ---------- {res.Hints[self.current_question][index]} \n"
        ret += "```"
        await ctx.send(ret)


