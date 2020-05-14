import os
import discord
import random

from discord.ext import commands
from dotenv import load_dotenv

import resources as res
import classes as cl

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = cl.Familiada()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def familiada(ctx):
    tosend = "```\nNa początek krótki dowcip\n"
    random.seed()
    number = random.randint(0, len(res.Puns) - 1)
    tosend += f"{res.Puns[number]}\nUdział w dzisiejszej grze biorą:\n```"
    for questions, answers, points in zip(res.Questions, res.Answers, res.Points):
        toAppend = cl.Question(questions, answers, points)
        bot.questions.append(toAppend)
    for team in bot.teams:
        tosend += f"{team}"
    await ctx.send(tosend)

@bot.command()
async def zbierz_druzyne(ctx, members: commands.Greedy[discord.Member]):
    number = random.randint(0, len(res.Colors) - 1)
    while number in bot.used_colors:
        number = random.randint(0, len(res.Questions) - 1)
    membs = {}
    for member in members:
        membs[member] = 0
    toappend = cl.Team(res.Colors[number], membs)
    bot.teams.append(toappend)
    bot.used_colors.append(number)
    await ctx.send(toappend)

@bot.command()
async def druzyny(ctx):
    ret = ""
    for team in bot.teams:
        ret += f"{team}"
    await ctx.send(ret)

@bot.command()
async def pytanie(ctx):
    # just in case
    if len(bot.asked_questions) == len(res.Questions):
        await ctx.send('nie mam do pana wiecej pytan')
        return
    # pick the question and send it
    # await ctx.send("Pytanie mnożone x1 xD```")
    number = random.randint(0, len(res.Questions) - 1)
    while number in bot.asked_questions:
        number = random.randint(0, len(res.Questions) - 1)
    question = bot.questions[number]
    bot.current_question = number
    bot.asked_questions.append(number)
    await ctx.send(question)
    # now wait for the answers
    bot.current_answers = []
    n = len(bot.asked_questions)
    while len(bot.current_answers) < len(question.answers):
        # check if a new question was asked, if it was, then return
        if n != len(bot.asked_questions):
            return
        score = 0
        # collecting answers until proper answer is sent
        guess = await bot.wait_for('message')
        if guess.content not in question.answers or guess.content in bot.current_answers:
            continue
        # finding the amount of points for the answer
        for index, answer in enumerate(question.answers, start = 0):
            if answer == guess.content:
                score = question.points[index]
                # add the guess to the answered list
                bot.current_answers.append(answer) 
        # finding the team to which the points should be added - and adding them
        for team in bot.teams:
            if guess.author in team.members:
                team.members[guess.author] += score
                team.points += score
        #something to send after an aswer has been guessed
        await ctx.send(f"```\nDobra odpowiedź {guess.author.display_name}! Ilość punktów: {score}```")
    #something to send after all answers have been guessed
    await ctx.send("```\nWszystkie odpowiedzi zostały odgadnięte!```")
    await ctx.send(question.printAnswered(bot.current_answers))

@bot.command()
async def podsumowanie(ctx):
    winner = bot.teams[0]
    for team in bot.teams:
        if team.points > winner.points:
            winner = team
    tosend = f"```\nZWYCIĘZCĄ DZISIEJSZEGO DNIA ZOSTAJE ZESPÓŁ {winner.name}!!!\nPodsumowanie:\n```"
    for team in bot.teams:
        tosend += f"{team}"
    await ctx.send(tosend)
    bot.teams = []
    bot.questions = []
    bot.used_colors = []
    print(bot.asked_questions)

@bot.command()
async def punkty(ctx):
    await ctx.send(bot.questions[bot.current_question].printAnswered(bot.current_answers))

bot.run(TOKEN)