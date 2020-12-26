# import the necessary modules
from discord.ext import commands
from client import Client


# create our class for our cog
class guildEvents(commands.Cog):

    # init code
    def __init__(self, client):

        # add our global client variable
        self.client: Client = client

    # add a listener for members joining a guild
    @commands.Cog.listener()
    async def on_member_join(self, member):

        # get the guild
        guild = member.guild

        # get the hackbans from the guild
        hackbans = self.client.fetch_hackbans(guild.id)

        # add all the hackban userids to a list
        hackbans = [x[1] for x in hackbans]

        # if the user is in the hackban list
        if member.id in hackbans:

            # ban the user
            await member.ban(reason='Hackbanned')


# setup method runs when the module is loaded
def setup(client):

    # add the cog to the client
    client.add_cog(guildEvents(client))
