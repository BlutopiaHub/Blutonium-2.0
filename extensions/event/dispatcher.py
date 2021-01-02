import discord

from discord.ext import commands
from blutopia import Client


# Create our main cog class
class dispatcher(commands.Cog):

    # init code
    def __init__(self, client):

        # create our global client variable
        self.client: Client = client

    @commands.Cog.listener()
    async def on_user_warn(self, guild: discord.Guild, user: discord.Member):
        
        # get the user's warns
        usermutes = self.client.fetch_warns(guild.id, user.id)

        # get the guild warn config
        autoban = self.client.guild_cache[guild.id]['warnconfig']['autoban']
        maxwarns = self.client.guild_cache[guild.id]['warnconfig']['maxwarns']

        # if autoban is on
        if autoban:

            if len(usermutes) >= maxwarns:
                
                # try to DM the user that he was banned
                try:

                
                    msg = await user.send(f"You have been banned in {guild} for having too many warns")

                except Exception:

                    pass


                # try and ban the user
                try:

                    await guild.ban(user, reason=f'[Blutonium Warning autoban] Warns exceeded {maxwarns}')
                
                # if we get an error
                except Exception:

                    # delete the dm we sent eariler
                    await msg.delete()

def setup(client):

    client.add_cog(dispatcher(client))