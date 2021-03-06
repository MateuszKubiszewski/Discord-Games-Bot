import discord
from discord.ext import commands

class Team:
    def __init__(self, _name, _members):
        self.name = _name
        self.members = _members
        self.points = 0
    # works for print(team) <=> str(team)
    def __str__(self):
        ret = f"```\n{self.name}\n"
        for member, score in self.members.items():
            ret += f"{member.display_name}: {score}\n"
        ret += f"Łączna liczba punktów: {self.points}\n```"
        return ret

class Question:
    def __init__(self, _content, answers_list, points_list):
        self.content = _content
        self.answers = answers_list
        self.points = points_list
    def __str__(self):
        ret = f"```\n{self.content}\n"
        for index, answer in enumerate(self.answers, start = 0):
            ret += f"{index + 1}. ---------- \n"
        ret += "```"
        return ret
    #def printAnswered(self, answered):
    #    ret = f"```\n{self.content}\n"
    #    for index, answer in enumerate(self.answers, start = 0):
    #        if answer in answered:
    #            ret += f"{index + 1}. {self.answers[index]}: {self.points[index]} \n"
    #        else:
    #            ret += f"{index + 1}. ---------- \n"
    #    ret += "```"
    #    return ret