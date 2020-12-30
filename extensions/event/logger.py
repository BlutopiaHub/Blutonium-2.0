# import the necessary packages
import discord
import datetime
import pg8000
from blutopia import Client
from discord.ext import commands
from discord.utils import get


# define the cog class
class logger(commands.Cog, name="logger"):

    # init code
    def __init__(self, client):

        self.client: Client = client

    # on_voice_state_update event
    @commands.Cog.listener()
    async def on_voice_state_update(self, usr: discord.Member, before, after):

        voicechannel = after.channel if before.channel is None else before.channel

        try:
            # try get the log data from the database from the "After" voice state
            logdata = self.client.fetch_log_data(voicechannel.guild)

        except pg8000.exceptions.Error as err:

            # print the error
            print(err)

            # if the "After" voice channel is None, get the log data from the "before" voice state
            logdata = self.client.fetch_log_data(before.channel.guild)

        # set the logs enabled variable
        isEnabled = logdata[1]

        # if logs are enabled, keep going
        if isEnabled:
            pass

        # if logs arent enabled end
        else:
            return

        # voice channel changing logger
        # if the users voice channel stayed the same
        if after.channel == before.channel:
            # continue
            pass
        else:

            # define all the log embeds
            emb1 = discord.Embed(title=f'{usr}',
                                 timestamp=datetime.datetime.utcnow(),
                                 colour=0x2F3136)

            emb2 = discord.Embed(title=f'{usr}',
                                 timestamp=datetime.datetime.utcnow(),
                                 colour=0x2F3136)

            emb3 = discord.Embed(title=f'{usr}',
                                 timestamp=datetime.datetime.utcnow(),
                                 colour=0x2F3136)

            # add the main field to all the embeds
            emb1.add_field(name="User changed voice channels",
                           value=f"*{before.channel}* -> *{after.channel}*")

            emb2.add_field(name="User left a voice channel",
                           value=f"{before.channel}")

            emb3.add_field(name="User joined a voice channel",
                           value=f"{after.channel}")

            # add the thumbnails for each embed
            emb1.set_thumbnail(url=usr.avatar_url)
            emb2.set_thumbnail(url=usr.avatar_url)
            emb3.set_thumbnail(url=usr.avatar_url)

            try:

                # get the log channel id 
                chanId = logdata[2]

                # get the log channel
                channel = get(before.channel.guild.channels, id=chanId)

                # if the after channel is none, They left the channel they were in
                if after.channel is None:
                    # send the log
                    return await channel.send(embed=emb2)

                # if the after channe isnt none they switched channels.
                else:
                    # send the log
                    return await channel.send(embed=emb1)

            # if we get an error its because the beore channel is None which means our channel variable would be
            # invalid. This also tells us that a user just joined a channel.
            except discord.HTTPException as err:

                # print the error
                print(err)

                # get the log channel id
                chanId = logdata[2]

                # set the channel variable to get it from the "after" voice state
                channel = get(after.channel.guild.channels, id=chanId)

                # send the log
                return await channel.send(embed=emb3)

        # mute logger
        # if the users mute state is the same
        if after.mute == before.mute:
            # continue
            pass
        else:

            # if the updated state is muted
            if after.mute:

                # make the embed
                emb = discord.Embed(title=f'{usr}',
                                    description='User server muted',
                                    timestamp=datetime.datetime.utcnow(),
                                    colour=0x2F3136)

                # set the embed thumbnail
                emb.set_thumbnail(url=usr.avatar_url)

            # if the updated state is not muted
            else:

                # make the embed
                emb = discord.Embed(title=f'{usr}',
                                    description='User un-server muted',
                                    timestamp=datetime.datetime.utcnow(),
                                    colour=0x2F3136)

                # set the embed thumbnail
                emb.set_thumbnail(url=usr.avatar_url)

            # get the log channel and send the log
            try:
                
                chanId = logdata[2]
                channel = get(after.channel.guild.channels, id=chanId)
                return await channel.send(embed=emb)
            
            except discord.HTTPException as err:
                
                # print the exception
                print(err)
                
                return

        # deaf logger
        # if the users deaf state is the same
        if after.deaf == before.deaf:
            # continue
            pass
        else:

            # if the updated state is deaf
            if after.deaf:

                # make the embed
                emb = discord.Embed(title=f'{usr}',
                                    description='User server deafend',
                                    timestamp=datetime.datetime.utcnow(),
                                    colour=0x2F3136)

                # set the embed thumbnail
                emb.set_thumbnail(url=usr.avatar_url)

            # if the updated state is not deaf
            else:

                # make the embed
                emb = discord.Embed(title=f'{usr}',
                                    description='User un-server deafened',
                                    timestamp=datetime.datetime.utcnow(),
                                    colour=0x2F3136)

                # set the embed thumbnail
                emb.set_thumbnail(url=usr.avatar_url)

            # get the log channel and send the log
            try:
                
                chanId = logdata[2]
                channel = get(after.channel.guild.channels, id=chanId)
                return await channel.send(embed=emb)
            
            except discord.HTTPException as err:
                
                # print the error
                print(err)
                
                return

    # on_message_delete event
    @commands.Cog.listener()
    async def on_message_delete(self, msg):

        # if the message author was a bot
        if msg.author.bot:
            # end
            return

            # get the log data from the database
        logdata = self.client.fetch_log_data(msg.guild)

        # set the logs enable variable
        isEnabled = logdata[1]

        # if logs are disabled, end
        if isEnabled:
            pass
        else:
            return

        moderator = None

        async for entry in msg.guild.audit_logs(limit=13,
                                                action=discord.AuditLogAction.message_delete):

            if entry.target == msg.author:

                moderator = entry.user
                break

            else:
                moderator = None

        # make the embed
        if moderator is None:
            emb = discord.Embed(title=f'{msg.guild}',
                                description=f'{msg.author.mention}\'s message in {msg.channel.mention} was deleted',
                                colour=0x2F3136,
                                timestamp=datetime.datetime.utcnow())
        else:
            emb = discord.Embed(title=f'{msg.guild}',
                                description=f'A message from {msg.author.mention} was deleted by ' +
                                            f'{moderator.mention} in {msg.channel.mention} ',
                                colour=0x2F3136,
                                timestamp=datetime.datetime.utcnow())

        # set all the embed fields and variables
        emb.add_field(name='Message Content',
                      value=f'{msg.content}',
                      inline=True)

        emb.set_footer(text=f'Msg ID: {msg.id}')

        emb.set_thumbnail(url=msg.author.avatar_url)

        try:
            # get the log channel id
            chanId = logdata[2]

            # get the log channel
            channel = get(msg.guild.channels, id=chanId)

            # send the log
            await channel.send(embed=emb)
        except discord.HTTPException as err:
            
            # print the error
            print(err)
            
            return

    # on_message_edit event
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):

        # if the before content is the same as the after content
        if before.content == after.content:
            # end
            return

        # if the user is a bot
        if before.author.bot:
            # end
            return

        # get the log data from the database
        logdata = self.client.fetch_log_data(before.guild)

        # set the logs enabled variable
        isEnabled = logdata[1]

        # if logs are disabled end
        if isEnabled:
            pass
        else:
            return

        # set the embed
        emb = discord.Embed(title=f'{before.author}',
                            description=f'A message was edited in {before.channel.mention}',
                            colour=0x2F3136,
                            timestamp=datetime.datetime.utcnow())

        # set all the embed components
        emb.add_field(name='Before',
                      value=f'{before.content}',
                      inline=True)

        emb.add_field(name='After',
                      value=f'{after.content}',
                      inline=True)

        emb.set_footer(text=f'Msg ID: {before.id}')

        emb.set_thumbnail(url=before.author.avatar_url)

        try:
            # get the log channel id
            chanId = logdata[2]

            # get the log channel
            channel = get(before.guild.channels, id=chanId)

            # send the log
            await channel.send(embed=emb)
            
        except discord.HTTPException as err:
            
            # print the error
            print(err)
            
            return

    # on_member_ban event
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):

        # placeholder code here
        return

    # on_member_unban event
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):

        # placeholder code here
        return


# setup function is called when the client loads the extension
def setup(client):
    client.add_cog(logger(client))
