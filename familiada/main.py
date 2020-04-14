import os
import discord
import random

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
    await ctx.send("""```python
                    Na początek krótki dowcip
                    ```""")
    random.seed()
    number = random.randint(0, len(res.Puns) - 1)
    await ctx.send(res.Puns[number])
    for questions, answers, points in zip(res.Questions, res.Answers, res.Points):
        toAppend = cl.Question(questions, answers, points)
        bot.questions.append(toAppend)

@bot.command()
async def zbierz_druzyne(ctx, *members):
    number = random.randint(0, len(res.Colors) - 1)
    while number in bot.used_colors:
        number = random.randint(0, len(res.Questions) - 1)
    bot.teams.append(cl.Team(res.Colors[number], members))
    bot.used_colors.append(number)
    await ctx.send(bot.teams[len(bot.familiada.teams) - 1])

@bot.command()
async def pytanie(ctx):
    # just in case
    if len(bot.asked_questions) == len(res.Questions):
        await ctx.send('nie mam do pana wiecej pytan')
        return
    # pick the question and send it
    await ctx.send("""```python
                    Pytanie mnożone x1 xD
                    ```""")
    number = random.randint(0, len(res.Questions) - 1)
    while number in bot.asked_questions:
        number = random.randint(0, len(res.Questions) - 1)
    question = bot.questions[number]
    bot.asked_questions.append(number)
    await ctx.send(question.content)
    # now wait for the answers
    answers = []
    while len(answers) < len(question.answers):
        score = 0
        # collecting answers until proper answer is sent
        guess = await bot.wait_for('message')
        if guess.content not in question.answers or guess.content in answers:
            continue
        # finding the amount of points for the answer
        for index, answer in enumerate(question.answers, start = 0):
            if answer == guess.content:
                score = question.points[index]
                # add the guess to the answered list
                answers.append(answer) 
        # finding the team to which the points should be added - and adding them
        for team in bot.teams:
            if guess.author in team.members:
                team.points += score
        #TO DO: something to send [wow! good answer! points: ]
        await ctx.send(f'wow xD, points: {score}')
    #TO DO: something to send after all answers have been guessed
    await ctx.send('all answs')

@bot.command()
async def wyczysc_familiade(ctx):
    pass

def punkty(bot):
    pass

def oglos_zwyciezce(bot):
    pass

bot.run(TOKEN)