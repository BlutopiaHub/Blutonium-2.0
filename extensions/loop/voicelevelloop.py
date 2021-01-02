import discord
import datetime

from discord.ext import commands, tasks
from discord.utils import get
from blutopia import Client
from collections import defaultdict


# define our main cog class
class voicelevels(commands.Cog):

    # init code
    def __init__(self, client):

        # define our global client variable
        self.client: Client = client

        # define our voiceusers as a set this variable
        # will store all users who were in a voice channel at the last check
        self.voiceUsers = defaultdict(dict)

        self.voice_client_loop.start()

    @tasks.loop(seconds=5)
    async def voice_client_loop(self):

        for guildid in self.voiceUsers.keys():

            users = self.voiceUsers[guildid]

            guild = get(self.client.guilds, id=guildid)

            for user in users:

                member = users[user]

                if member.voice.deaf or member.voice.self_deaf \
                    or member.voice.mute or member.voice.self_mute \
                        or member.voice.afk:

                    return

                print(member)
                self.client.leveluser(user, guildid)

        # for every guild in the client guilds

        for guild in self.client.guilds:

            self.voiceUsers[guild.id] = {}

            for channel in guild.voice_channels:

                for member in channel.members:

                    self.voiceUsers[guild.id][member.id] = member


def setup(client):

    client.add_cog(voicelevels(client))
