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
        self.trans = {"`": r"\`"}

    # on_voice_state_update event
    @commands.Cog.listener()
    async def on_voice_state_update(self, usr: discord.Member, before: discord.VoiceState, after: discord.VoiceState):

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

                if after.channel is None:

                    # get the log channel
                    channel = get(before.channel.guild.channels, id=chanId)

                if before.channel is None:

                    # get the log channel
                    channel = get(after.channel.guild.channels, id=chanId)


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
            except Exception as err:
                
                # print our error
                print(err)

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

                if before.channel is None:

                    channel = get(after.channel.guild.channels, id=chanId)


                if after.channel is None:

                    channel = get(before.channel.guild.channels, id=chanId)    
            
                return await channel.send(embed=emb)
            
            except Exception as err:
                
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

                if before.channel is None:

                    channel = get(after.channel.guild.channels, id=chanId)

                if after.channel is None:

                    channel = get(before.channel.guild.channels, id=chanId)

                return await channel.send(embed=emb)
            
            except Exception as err:
                
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
            emb = discord.Embed(title=f'Message Delete Log',
                                description=f'{msg.author.mention}\'s message in {msg.channel.mention} was deleted\n\n'
                                            f'***Message Content***\n'
                                            f'```{msg.content.translate(str.maketrans(self.trans))}```',
                                colour=0x2F3136,
                                timestamp=datetime.datetime.utcnow())
        else:
            emb = discord.Embed(title=f'{msg.guild}',
                                description=f'A message from {msg.author.mention} was deleted by ' +
                                            f'{moderator.mention} in {msg.channel.mention}\n\n'
                                            f'***Message Content***\n'
                                            f'```{msg.content.translate(str.maketrans(self.trans))}```',
                                colour=0x2F3136,
                                timestamp=datetime.datetime.utcnow())

        emb.set_footer(text=f'Msg ID: {msg.id} User ID: {msg.author.id}')
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

        # create the embed
        emb = discord.Embed(title=f'Message Edit Log',
                            description=f'[A message]'
                                        f'(https://discord.com/channels/'
                                        f'{before.guild.id}/{before.channel.id}/{before.id})'
                                        f' was edited in {before.channel.mention}\n\n***Before***\n'
                                        f'```{before.content.translate(str.maketrans(self.trans))}```\n***After***\n'
                                        f'```{after.content.translate(str.maketrans(self.trans))}```',

                            colour=0x2F3136,
                            timestamp=datetime.datetime.utcnow())

        emb.set_footer(text=f'Msg ID: {before.id} User ID: {before.author.id}')
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

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):

        # for all the last 13 ban audit logs
        async for entry in guild.audit_logs(limit=13, action=discord.AuditLogAction.ban):

            # if the user that was banned is the same user that was banned in our event
            if entry.target.id == user.id:

                # if the user that banned the user is ourself
                if entry.user.id == self.client.user.id:

                    # return because the event was already dispatched
                    return

                # if were not the ones who banned them, we will need some info from the ban for the dispatch
                else:

                    # get the reason for the ban
                    reason = entry.reason

                    # get the moderator that banned the user
                    moderator = entry.user

                    # dispatch our custom member banend event with our botban variable as false
                    return self.client.dispatch('member_banned', guild, user, moderator, reason)

    # on_member_ban event
    @commands.Cog.listener()
    async def on_member_banned(self, guild, member, mod, reason):

        # set our moderator variable to the mention of the moderator if the moderator is not None
        moderator = mod.mention if mod is not None else "Someone I could not find."

        # set our reason variable to a string of None if its none
        reason = "None" if reason is None else reason

        # create our embed for the ban entry
        embed = discord.Embed(title='Member Ban log',
                              description=f'<@{member.id}> ({member}) was banned by {moderator}\n'
                                          f'\n**Reason**\n```{reason}```',
                              color=0x2F3136,
                              timestamp=datetime.datetime.utcnow())

        # add the avatar url as the thumbnail
        embed.set_thumbnail(url=member.avatar_url)

        # get the logging channel
        logchannelid = self.client.guild_cache[guild.id]['logchannelid']
        logchannel = get(guild.text_channels, id=logchannelid)

        # get the log status
        logstatus = self.client.guild_cache[guild.id]['logsenabled']

        # if logging is on
        if logstatus:

            # send the log
            await logchannel.send(embed=embed)

        return

    # on_member_unban event
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):

        # create our embed for the ban entry
        embed = discord.Embed(title='Member Unban log',
                              description=f'<@{user.id}> ({user}) was unbanned from the guild',
                              color=0x2F3136,
                              timestamp=datetime.datetime.utcnow())

        # add the avatar url as the thumbnail
        embed.set_thumbnail(url=user.avatar_url)

        # get the logging channel
        logchannelid = self.client.guild_cache[guild.id]['logchannelid']
        logchannel = get(guild.text_channels, id=logchannelid)

        # get the log status
        logstatus = self.client.guild_cache[guild.id]['logsenabled']

        # if logging is on
        if logstatus:
            # send the log
            await logchannel.send(embed=embed)

        # stop the code
        return

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        # for all the last 13 ban audit logs
        async for entry in member.guild.audit_logs(limit=13, action=discord.AuditLogAction.kick):

            # if any of the kicked members are the user that just left
            if entry.target.id == member.id:

                # if blutonium was the one that kicked them
                if entry.user.id == self.client.user.id:

                    # the event has already been dispatched
                    return

                # if it was someone else then we need to dispatch the event
                else:

                    # get the reason for the kick
                    reason = entry.reason

                    # get the moderator that kicked the user
                    mod = entry.user

                    # send the event
                    return self.client.dispatch('member_kicked', member.guild, member, mod, reason)

    @commands.Cog.listener()
    async def on_member_kicked(self, guild, member, mod, reason):

        # set our moderator variable to the mention of the moderator if the moderator is not None
        moderator = mod.mention if mod is not None else "Someone I could not find."

        # set our reason variable to a string of None if its none
        reason = "None" if reason is None else reason

        # create our embed for the ban entry
        embed = discord.Embed(title='Member Kick log',
                              description=f'<@{member.id}> ({member}) was kicked by {moderator}\n'
                                          f'\n**Reason**\n```{reason}```',
                              color=0x2F3136,
                              timestamp=datetime.datetime.utcnow())

        # add the avatar url as the thumbnail
        embed.set_thumbnail(url=member.avatar_url)

        # get the logging channel
        logchannelid = self.client.guild_cache[guild.id]['logchannelid']
        logchannel = get(guild.text_channels, id=logchannelid)

        # get the log status
        logstatus = self.client.guild_cache[guild.id]['logsenabled']

        # if logging is on
        if logstatus:

            # send the log
            await logchannel.send(embed=embed)

        return


# setup function is called when the client loads the extension
def setup(client):
    client.add_cog(logger(client))
