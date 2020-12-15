# import the necessary modules
from discord.ext import commands, tasks
from client import Client
from discord.utils import get
import discord, datetime

# Create our Cog class
class moderationLoops(commands.Cog):

    # init code
    def __init__(self, client):

        # set the global client variable
        self.client : Client = client

        # this will start the unmute loop method. 
        self._unmuteloop.start()
    
    # Override Cog_unload so that when the cog is unloaded the unmute loop can be stopped
    def cog_unload(self):
        
        # stop the unmute loop
        self._unmuteloop.stop()

    @tasks.loop(seconds=1)
    async def _unmuteloop(self):

        # wait until the client is ready and all the caches are built
        await self.client.wait_until_ready()

        # fetch all the guilds that the bot is in
        guilds = self.client.guilds

        # for every guild
        for guild in guilds:

            # get the mute list
            mutelist = self.client.fetch_active_mutes(guild.id)

            # for evey active mute
            for mute in mutelist:

                # turn the data fetched from our cache into their own variables
                userid = mute[1]
                reason = mute[2]
                time = mute[3]
                modid = mute[4]

                # if the time at  which the mute ends has passed
                if time < datetime.datetime.now():
                    
                    # get the mute role for the server
                    muterole = await self.client.fetch_mute_role(guild)
                    
                    # fetch the user
                    user = get(guild.members, id = userid)

                    # remove the mute from the database and cache
                    self.client.unmute(guild.id, userid)

                    # if our user variable is None that measn the user left the server
                    if user is None:

                        # just continue on with the loop
                        continue
                        
                    # if anything else
                    else:  

                        # try and unmute the user
                        await user.remove_roles(muterole)


def setup(client):

    client.add_cog(moderationLoops(client))