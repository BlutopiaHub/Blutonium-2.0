# import the required packages
import discord
import itertools
from discord.ext import commands, tasks


# define the cog class.
class presence(commands.Cog, name='presenceProc'):

    # init code
    def __init__(self, client):

        self.client = client

        self.statusIndex = [0, 1, 2, 3, 4]

        # set the displaying status variable as an intertools cycle
        self.displaying = itertools.cycle(self.statusIndex)
        
        # add the prsence loop to the client
        self._changePresence.start()

    # When the cog is unloaded, run this method.
    def cog_unload(self):
        self._changePresence().stop()

    # presence activity method
    @tasks.loop(seconds=20)
    async def _changePresence(self):

        # wait until all the discord.py caches and such are built
        await self.client.wait_until_ready()
                
        # get the total # of bot users
        botusers = len(set(self.client.get_all_members()))

        # get the total # of guilds
        guilds = len(self.client.guilds)

        # define all the statuses
        statuses = [(f'over {botusers} users!', discord.ActivityType.watching),
                    (f'over {guilds} guilds!', discord.ActivityType.watching),
                    ('Forgot your prefix? @mention me!', discord.ActivityType.watching),
                    ('over your mind', discord.ActivityType.watching),
                    ('BLUTONIUM 2.0.0 UPDATE!', discord.ActivityType.playing)]

        # set the current status as the next index in the cycle
        current_status = statuses[next(self.displaying)]

        # change the client status
        await self.client.change_presence(status=discord.Status.online,
                                          activity=discord.Activity(name=current_status[0],
                                                                    type=current_status[1]))


# setup function is called when the client loads the extension.
def setup(client):
    client.add_cog(presence(client))
