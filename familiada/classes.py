from discord.ext import commands

# TO DO
# str magic method for Familiada, Team, Question
# functions to clean the Bot class, proclaim the winner

# wysietlanie:
# wszystkich teamow po inicjalizacji Familiady
# punktacji przed i po pytaniu
# punktacji pytania po zgadnieciu wszystkich odpowiedzi
# punktacja na zadanie
# podpowiedzi < no powodzenia zycze

class Familiada(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='@')
        self.teams = []
        self.questions = []
        self.asked_questions = []
        self.used_colors = []

class Team:
    def __init__(self, _name, _members):
        self.name = _name
        self.members = _members
        self.points = 0

class Question:
    def __init__(self, _content, answers_list, points_list):
        self.content = _content
        self.answers = answers_list
        self.points = points_list


