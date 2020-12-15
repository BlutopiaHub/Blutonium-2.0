from datetime import date
from discord import member
from discord import user
from discord.ext import commands
import discord, datetime, time, re, requests, json, pytz
from discord.utils import get
import humanize as h
from setup import TOKEN
from collections import  defaultdict
from client import Client

def request_discord_user(userid):
    base_url= 'https://discord.com/api/v8'
    headers = {'Authorization': 'Bot ' + f'{TOKEN}'}
    search_url = base_url + f'/users/{userid}'
    response = requests.get(search_url, headers=headers)

    return response

# define the main cog class
class moderation(commands.Cog, name='Moderation'):

    """
    Moderation Commands
    """

    # init code 
    def __init__(self, client):

        # set our global client variables
        self.client : Client = client

        # create the task for getting the emojis
        client.loop.create_task(self._getEmojis())

    # get emojis method We use this beacause the methods we use can only be used when the client is ready and we need to use corotines
    async def _getEmojis(self):

        # wait unitl the client is ready
        await self.client.wait_until_ready()

        # support server to get the emojis
        self.support = get(self.client.guilds, name="Blutonium updates and support", id=629436501964619776, owner_id=393165866285662208)

        # Check emoji
        self.checkemoji = get(self.support.emojis, name="BlutoCheck")

        # X emoji
        self.crossemoji = get(self.support.emojis, name="BlutoX")

        # logo emoji
        self.blutonium = get(self.support.emojis, name="Blutonium")
    
    # -----------------COMMANDS-----------------------------------
    # For every command we have a @commands.command decorator that declares the method as a command. 
    # We also have a @commands.check_any decorator, This decorator takes the user and applies specified checks

    # TODO re-add Admin roles
    # TODO expand logging cfg

    # the CFG command group are subcommands to configure and customize everything on blutonium!
    @commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
    @commands.group(name='config', aliases=['cfg', 'settings'], help='Configure everything that blutonium can do!')
    async def _config(self,ctx:commands.Context):

        # if no subcommands are invoked
        if ctx.invoked_subcommand is None:
            
            # get the guild prefix
            prefix = self.client.fetch_prefix(ctx.guild.id)

            # get the guild log data
            logdata = self.client.fetch_log_data(ctx.guild)

            # create an embed  
            emb = discord.Embed(title=f'{ctx.guild} Configuration')

            # add the guild icon as the thumbnail
            emb.set_thumbnail(url=ctx.guild.icon_url)

            # set the prefix field
            emb.add_field(name=f'Guild Prefix', value=prefix, inline=True)

            # get the logging channel id
            logchannelid = logdata[2]

            # find the channel using the id
            logchannel = get(ctx.guild.text_channels, id=logchannelid)

            # set the logs channel field
            emb.add_field(name=f'Guild Logging Channel', value=f'{logchannel.mention}', inline=True)

            # get the logsenabled boolean
            logsenabled = logdata[1]

            # add the logs enabled field
            emb.add_field(name=f'Logging Enabled', value=f'{logsenabled}', inline=True)

            # add the admin roles field
            emb.add_field(name='Admin roles', value=f'Use ``{prefix}cfg adminroles list`` to list the guild admin roles', inline=True)

            await ctx.send(embed=emb)

    # cfg -> prefix subcommand is to change the prefix in the guild
    @_config.command(name='prefix', aliases=['setprefix', 'changeprefix'], help='Change the guild\'s prefix')
    async def _prefix(self,ctx,prefix):

        # get previous prefix
        previous = self.client.fetch_prefix(ctx.guild.id)

        # get the new prefix from input
        new = prefix

        # update the guild prefix
        update = self.client.update_prefix(ctx.guild.id, prefix)

        # Create the feedback embed
        emb = discord.Embed(title=f'{ctx.guild}', description='The prefix for this guild was changed!', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())

        # Add the fields which illustrate the prefix change
        emb.add_field(name='Previous prefix', value=f'{previous}')
        emb.add_field(name='New prefix', value=f'{new}')

        # send the embed 
        await ctx.channel.send(embed=emb)
    
    # cfg -> logchannel subcommand is to change the loggign channel in the guild
    @_config.command(name='logchannel', aliases=['logc', 'logchan'], help='Change the channel where the bot will send logs')
    async def _logchannel(self,ctx,channelid):

        # try get the old log channel
        try:

            # get the log channel id
            oldlogchannel = int(self.client.fetch_log_data(ctx.guild)[2])
            
            # get the actual channel
            oldlogchannel = get(ctx.guild.text_channels, id=oldlogchannel)
        
        # if we get an error the log channel is invalid
        except:
            
            # set the variable to None since its gonna be used in the embed at the end
            oldlogchannel = None

        # try and turn the input into an INT
        try:

            # parse the string into an INT    
            NewLogChannel = int(channelid)

        # if we get an error doing this its because the user did not input a Valid Number
        except:

            # return an error message
            return await ctx.send(f"{self.crossemoji} **Please input a valid chanel ID to change to**")

    
        # get the channel from the guild channels array
        NewLogChannel = get(ctx.guild.text_channels, id=NewLogChannel)

        # since our get() method returns None if it cant fin the channel we will return an error message if the method returns None
        if NewLogChannel is None:

            # send our error message
            return await ctx.send(f"{self.crossemoji} **Could not find that channel!**")

        # if our old log channel is the same as the new one theres literally no point in doing this
        if oldlogchannel == NewLogChannel:

            # send our error message
            return await ctx.send(f"{self.crossemoji} **The log channel is already set to {NewLogChannel.mention} **")

        # set the log channel and send the feedback embed
        try:

            # set the log chhannel
            self.client.update_log_channel(ctx.guild, NewLogChannel.id)

            # create the feedback embed
            emb = discord.Embed(title=f'{ctx.guild}', description='The log channel for this guild was changed!', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())

            # Add the field for the change

            # if the old log channel is not None
            if oldlogchannel is not None:

                # add the normal field
                emb.add_field(name='Change', value=f'**{oldlogchannel.mention} -> {NewLogChannel.mention}**')
            
            # if it is none
            else:

                # add the field with None as the old channel
                emb.add_field(name='Change', value=f'**None -> {NewLogChannel.mention}**')

            await ctx.send(embed=emb)

        except Exception as err:
            await ctx.send(f"❌ Failled to set logs channel: {err}")

    # cfg -> togglelogs subcommand is to toggle logs in the guild
    @_config.command(name='togglelogs', aliases=['logs', 'tlogs'], help='Disable or Enable logging in this guild')
    async def _togglelogs(self,ctx):

        # toggle the logs
        res = self.client.toggle_logs(ctx.guild.id)

        # since our togglelogs method returns the new state of logs we can use it for our feedback messge
        
        # if our new state is true that means our logs have just been enabled.
        if res:

            # send feedback 
            await ctx.send(f"{self.checkemoji} **Logs have been enabled**")

        # if our new state is Fasle that means our logs have just beed disabled.
        else:

            # send feedback
            await ctx.send(f"{self.crossemoji} **Logs have been disabled**")

    # Ban command is to ban a member from the guild
    @commands.check_any(commands.has_permissions(ban_members=True), commands.is_owner())
    @commands.command(name = 'ban',aliases=[], help='Strike the BAN HAMMER.', usage='`[Userid or Mention]` `[Reason]`')
    async def _ban(self, ctx, *args):
        
        # try to ban the member
        try:

            # if the silent arg is present
            if args[0].lower() == '-s':
                
                # get the member input 
                inp = args[1]

                # get the rest of the args as the reason
                reason = " ".join(args[2:])

                # get the member
                member = self.client.fetch_simple_member(ctx, inp)

                if ctx.author.roles[-1].position < member.roles[-1].position:
                    emb = discord.Embed(title=f"{self.crossemoji} Member could not be banned!",colour=0xFCFCFC)
                    emb.add_field(name="Error", value=f"``You don't have permission to do that!``")
                    return await ctx.send(emb=emb)
                # ban the user
                await member.ban(reason=f'[{ctx.author}] {reason}')

                # try and delete the message invoking the command
                try:
                    await ctx.message.delete()
                
                # if we cant delete it 
                except:
                    
                    # stop the code.
                    return

                # a slient ban wont sent the user a dm and it wont send an embed in the server. It will also delete the authors message invokeing the command. 
                # This is to attract less attension when banning a user

                # to stop anything else from running after a silent ban we need a return at the end
                return

            # if it isnt present
            else:

                # get the member input
                inp = args[0]
            

                # get the rest of the args as the reson
                reason = " ".join(args[1:])

                # get the member
                member : discord.Member = self.client.fetch_simple_member(ctx,inp)

                if ctx.author.roles[-1].position < member.roles[-1].position:
                    emb = discord.Embed(title=f"{self.crossemoji} Member could not be banned!",colour=0xFCFCFC)
                    emb.add_field(name="Error", value=f"``You don't have permission to do that!``")

                    return await ctx.send(embed=emb)

                msg = None
                # try and dm the user
                try:

                    msg : discord.Message = await member.send(f"You've been banned in {ctx.guild} for: ``{reason}``")
                    userdm = True

                # if the client cant dm the member
                except:
            
                    # set the userdm variable as false (We will need this variable later.)
                    userdm = False

                # try and ban the user
                try:
                    ban = await member.ban(reason=reason)
                # if the ban doesnt work.
                except Exception as err:
                    
                    # try and delete the sent DM to the user
                    try:
                        await msg.delete()
                    # in the event of an eror
                    except:
                        # do nothing
                        pass

                    # create the error embed
                    emb = discord.Embed(title=f"{self.crossemoji} Member could not be banned!",colour=0xFCFCFC)
                    emb.add_field(name="Error", value=f"``{err}``")
                    await ctx.send(embed = emb)
                    return
                
                # create and send the ban succesful embed
                try:

                    # initialize the embed and add the fields
                    embed = discord.Embed(title=f"{self.checkemoji} Member banned succesfully",colour=0xFCFCFC, description=f"{member.mention}")
                    embed.add_field(name="Reason", value=reason, inline=True)
                    embed.add_field(name="Member ID", value=member.id, inline=True)
                    
                    # if the userdm variable is false that means we could not dm the user. We will add that information to the embed.
                    if userdm == False:
                        embed.add_field(name="Errors", value="Failed to send User a DM", inline=False)

                    # set the thumbnail of the embed to the user avatar 
                    embed.set_thumbnail(url=member.avatar_url)
                    
                    # send the embed
                    await ctx.send(embed=embed)

                # if we get an error its most likley because the reason variable is empty and we cant have an empty value in a embed field
                except Exception as err:

                    # initialize the new embed
                    embed = discord.Embed(title=f"{self.checkemoji} Member banned succesfully",colour=0xFCFCFC, description=f"{member.mention}")

                    # in this case we will just set the reason field to "None" so we get no errors
                    embed.add_field(name="Reason", value="None", inline=True)

                    # do the same for the rest of the embed
                    embed.add_field(name="Member ID", value=member.id, inline=True)

                    if userdm == False:
                        embed.add_field(name="Errors", value="Failed to send User a DM", inline=False)

                    embed.set_thumbnail(url=member.avatar_url)

                    # send the new embed.
                    await ctx.send(embed=embed)

        # if we get an IndexError that means the user did not input someone to ban.
        except IndexError as err:

            await ctx.send(f"{self.crossemoji} **Please input a user to BAN**")

    # unban command is to unban a member from the guild
    @commands.check_any(commands.has_permissions(ban_members=True), commands.is_owner())
    @commands.command(name='unban',aliases=['uban', 'pardon'], help='Pardon a banned member in the server.', usage='`[Name+Tag or Userid]`')
    async def _unban(self, ctx, *args):
    
        # get all the bans in the server and put it into an array
        bans = []

        # for every ban in the guild
        for ban in await ctx.guild.bans():

            # add the ban to the bans array
            bans.append(ban[1])

        # define the user input
        inp = args[0]

        # get the user from the input
        try:
            
            # fetch the member from the bans using the userid
            member : discord.Member = get(bans, id=int(inp))

        # if theres an error the input could not be turned into an Int32. In that case the user didnt unput an ID to unban So lets check if they put a name and tag
        except:
        
            try:
                # get the user input and split it into an array at the #
                userinp = inp.split('#')

                # set the tag and username as variables
                Username = userinp[0]

                # over here we turn the tag into an INT so that if the tag has letters for some reason it returns an error and we know that the user did not input the name of the user correctly.
                Tag = int(userinp[1])
                
                
                # Try and find the user
                member : discord.Member = get(bans, name=Username, discriminator=str(Tag) )

            except Exception as err:

                member = None

        # if the member variable is still none...
        if member == None:

            # stop the code and send that the user is not found...
            return await ctx.send(f"{self.crossemoji} **User not found in bans!**")

        # try and unban the user
        try:
        
            ban = await ctx.guild.unban(member)

        # if theres an error    
        except Exception as err:

            # make an embed
            emb = discord.Embed(title=f"{self.crossemoji} Member could not be unbanned", color=0xFCFCFC)

            # add the error to the embed
            emb.add_field(name="Error",value=f"``{err}``")

            # send the embed
            await ctx.send(embed=emb)

            # stop the code
            return
        
        # Create and send the succesful embed
        try:

            # Create the embed
            banembed = discord.Embed(title=f"{self.checkemoji} Member Unbanned succesfully", description=f"{member.mention}", color=0xFCFCFC)

            # Add the user id field
            banembed.add_field(name="ID",value=member.id,inline=True)

            # Set the thumbnail as the user avatar
            banembed.set_thumbnail(url=member.avatar_url)

            # Send the embed
            await ctx.send(embed=banembed)

        except Exception as err: 
            
            ctx.send(f"{self.checkemoji} **User was unbanned**")

    # Kick command is to kick a member from the guild
    @commands.check_any(commands.has_permissions(kick_members=True), commands.is_owner())
    @commands.command(name="kick",aliases=["boot"], help='Kick a user from the server.', user='`[Userid or Mention]` `[Reason]`')
    async def _kick(self, ctx, *args):
        
        # try to kick the member
        try:

            # if the silent arg is present
            if args[0].lower() == '-s':
                
                # get the member input 
                inp = args[1]

                # get the rest of the args as the reason
                reason = " ".join(args[2:])

                # get the member
                member : discord.Member = self.client.fetch_member(ctx,inp)

                if ctx.author.roles[-1].position < member.roles[-1].position:
                    emb = discord.Embed(title=f"{self.crossemoji} Member could not be kicked!",colour=0xFCFCFC)
                    emb.add_field(name="Error", value=f"``You don't have permission to do that!``")
                    return await ctx.send(emb=emb)
                # kick the user
                await member.kick(reason=reason)

                # try and delete the message invoking the command
                try:
                    await ctx.message.delete()
                
                # if we cant delete it 
                except:
                    
                    # stop the code.
                    return

                # a slient kick doesnt send the user a dm and it wont send an embed in the server. It will also delete the authors message invokeing the command. 
                # This is to attract less attension when kicking a user

                # to stop anything else from running after a silent kick we need a return at the end
                return

            # if it isnt present
            else:

                # get the member input
                inp = args[0]
            

                # get the rest of the args as the reson
                reason = " ".join(args[1:])

                # get the member
                member : discord.Member = self.client.fetch_member(ctx,inp)

                if ctx.author.roles[-1].position < member.roles[-1].position:
                    emb = discord.Embed(title=f"{self.crossemoji} Member could not be kicked!",colour=0xFCFCFC)
                    emb.add_field(name="Error", value=f"``You don't have permission to do that!``")

                    return await ctx.send(emb=emb)

                msg = None                    
                # try and dm the user
                try:

                    msg : discord.Message = await member.send(f"You've been kicked in {ctx.guild} for: ``{reason}``")
                    userdm = True

                # if the client cant dm the member
                except:
            
                    # set the userdm variable as false (We will need this variable later.)
                    userdm = False

                # try and kick the user
                try:
                    kick = await member.kick(reason=reason)
                # if the kick doesnt work.
                except Exception as err:
                    
                    # try and delete the sent DM to the user
                    try:
                        await msg.delete()
                    # in the event of an eror
                    except:
                        # do nothing
                        pass

                    # create the error embed
                    emb = discord.Embed(title=f"{self.crossemoji} Member could not be kicked!",colour=0x36393F)
                    emb.add_field(name="Error", value=f"``{err}``")
                    await ctx.send(embed = emb)
                    return
                
                # create and send the kick succesful embed
                try:

                    # initialize the embed and add the fields
                    embed = discord.Embed(title=f"{self.checkemoji} Member kicked succesfully",colour=0x36393F, description=f"{member.mention}")
                    embed.add_field(name="Reason", value=reason, inline=True)
                    embed.add_field(name="Member ID", value=member.id, inline=True)
                    
                    # if the userdm variable is false that means we could not dm the user. We will add that information to the embed.
                    if userdm == False:
                        embed.add_field(name="Errors", value="Failed to send User a DM", inline=False)

                    # set the thumbnail of the embed to the user avatar 
                    embed.set_thumbnail(url=member.avatar_url)
                    
                    # send the embed
                    await ctx.send(embed=embed)

                # if we get an error its most likley because the reason variable is empty and we cant have an empty value in a embed field
                except Exception as err:

                    # initialize the new embed
                    embed = discord.Embed(title=f"{self.checkemoji} Member kicked succesfully",colour=0x36393F, description=f"{member.mention}")

                    # in this case we will just set the reason field to "None" so we get no errors
                    embed.add_field(name="Reason", value="None", inline=True)

                    # do the same for the rest of the embed
                    embed.add_field(name="Member ID", value=member.id, inline=True)

                    if userdm == False:
                        embed.add_field(name="Errors", value="Failed to send User a DM", inline=False)

                    embed.set_thumbnail(url=member.avatar_url)

                    # send the new embed.
                    await ctx.send(embed=embed)

        # if we get an IndexError that means the user did not input someone to kick.
        except IndexError as err:

            await ctx.send(f"{self.crossemoji} **Please input a user to KICK**")

    # TODO FIX THIS FOR ALL SERVERS PLUS ADD CFG FOR AUTOBAN
    """
    # warn command to warn users
    @commands.check_any(commands.has_permissions(ban_members=True), commands.check(check_modchannel))
    @commands.command(name='warn', help='Warn a user.', usage='`[Userid or Mention]` `[Reason]`')
    async def _warn(self,ctx,user,*,reason="No reason provided"):

        # get the user
        user = self.client.fetch_simple_member(ctx, user)

        if user is None:

            return await ctx.send("❌ **User not found!**")


        # get the ammount of warns that the user has 
        warns = getwarns(user.id)

        # if the invokers top role is below the users top role
        if ctx.author.roles[-1].position < user.roles[-1].position:

            # the invoker isnt allowed to warn someone above them
            emb = discord.Embed(title=f"{self.crossemoji} Member could not be warned!",colour=0xFCFCFC)
            emb.add_field(name="Error", value=f"``You don't have permission to do that!``")

            # send the embed and end the code
            return await ctx.send(embed = emb)

        # create the warn case id
        caseid = int(time.time())

        # add the warn 
        addwarn(ctx, user.id, reason, caseid)

        # create the feedback for the moderator
        emb = discord.Embed(title="✅ Warn sent successfully", color=0xFCFCFC)
        emb.set_thumbnail(url=user.avatar_url)
        emb.add_field(name=f"{user}", value=f"ID: {user.id}\nWarns: {len(warns)} (+1)", inline=True)
        emb.add_field(name='Warn', value=f"Reason: {reason}\nCase ID: {caseid}")

        await ctx.send(embed=emb)

        # create the warning notifier embed
        emb = discord.Embed(title=f"Warning", description="You've recieved a warning.", color=0xFCFCFC, timestamp=datetime.datetime.utcnow())
        emb.add_field(name='reason', value=reason)

        # send the notify to the user
        await user.send(embed=emb)

    # warns command to list a users warn
    @commands.check_any(commands.has_permissions(ban_members=True), commands.check(check_modchannel))
    @commands.command(name='warns', aliases=['warn-list'], help='List a user\'s warns.', usage='`[Userid or Mention]`')
    async def _warns(self,ctx,user):

        # make fake  user class for convenicnce later
        class fakeMod():

            def __init__(self):

                self.mention = "Not found!"

        # get the user
        user = getusersimple(ctx, user)

        if user is None:

            return await ctx.send("❌ **User not found!**")    

        # get the users warns 
        warns = getwarns(user.id)

        # create the embed 
        emb = discord.Embed(title=f'{user} warns', description=f'User has {len(warns)} warns', color=0xFCFCFC)
        emb.set_thumbnail(url=user.avatar_url)

        # create fields for each warn
        for x in warns:

            # get the mod that warned the user
            if x[4] is None:
                mod = fakeMod()
            else:
                mod = get(ctx.guild.members, id=x[4])

            emb.add_field(name=f"Warn #{x[0]}", value=f'Reason: {x[2]}\nCase ID: {x[3]}\nIssuer: {mod.mention}')

        # send the embed
        await ctx.send(embed=emb)
    
    # warns-given commands is to list all the warns taht the moderator has given
    @commands.check_any(commands.has_permissions(ban_members=True), commands.check(check_modchannel))
    @commands.command(name='warns-given', aliases=['gwarns'], help="List all the warns that you have issued")
    async def _warns_given(self,ctx):
        # make fake  user class for convenicnce later
        class fakeUser():

            def __init__(self):

                self.mention = "Not found!"


        # get the users warns 
        warns = getgivenwarns(ctx.author.id)

        # create the embed 
        emb = discord.Embed(title=f'{ctx.author} warns given', description=f'User has issued {len(warns)} warns', color=0xFCFCFC)
        emb.set_thumbnail(url=ctx.author.avatar_url)

        # create fields for each warn
        for x in warns:

            # get the mod that warned the user
            if x[1] is None:
                user = fakeUser()
            else:
                user = get(ctx.guild.members, id=x[1])

            if user is None:

                user = fakeUser()

            emb.add_field(name=f"Warn #{x[0]}", value=f'**Reason:** {x[2]}\n**Case ID:** {x[3]}\n**Issued to:** {user.mention}')

        # send the embed
        await ctx.send(embed=emb)

    # warn-remove command to remove a warn
    @commands.check_any(commands.has_permissions(ban_members=True), commands.check(has_mod), commands.check(check_modchannel))
    @commands.command(name='warn-remove', aliases=['warn-delete', 'remwarn', 'warndel'], help='Remove a warn from a user.', usage='`[CaseID]`')
    async def _warnRemove(self,ctx,caseId):

        # get all the warns
        warns = fetchAllWarns()

        # set the variable for the target warn to delete
        Delwarn = None

        # set the target warn to this warn if the warnID is equal to the selected warnID
        for warn in warns: 
            if warn[3] == int(caseId):
            
                Delwarn = warn 

        if Delwarn is None:
            await ctx.send("❌ **Warn not found!**")
        else:
            remwarn(Delwarn[3])
            emb = discord.Embed(title='✅ Warn Deleted', color=0xFCFCFC)
            emb.add_field(name=f"Warn #{Delwarn[0]}", value=f'Reason: {Delwarn[2]}\nCase ID: {Delwarn[3]}' )
            await ctx.send(embed=emb)

    """

    # mute command to mute a user
    @commands.check_any(commands.has_permissions(manage_roles=True), commands.is_owner())
    @commands.command(name='mute', aliases=[], help='Mute a user in the server.', usage='`[Userid or Mention]` `[Time]` `[Reason]`')
    async def _mute(self,ctx,user,duration='2h', *, reason='None given'):

        # get the user from the input
        user = self.client.fetch_simple_member(ctx,user)

        # if the invokes top role is under the users top role
        if ctx.author.roles[-1].position < user.roles[-1].position:

            # the invoker does not have permission to mute the user
            emb = discord.Embed(title=f"{self.crossemoji} Member could not be muted!",colour=0xFCFCFC)
            emb.add_field(name="Error", value=f"``You don't have permission to do that!``")
            return await ctx.send(embed=emb)        

        # get the current time
        now = datetime.datetime.now()

        # Split the letters from the numbers in our duration
        duration = re.split('(\d+)', duration)

        try:
            print(duration)
            # our time will be the number
            time = int(duration[1])

            # our unit will be the letters
            unit = duration[2]

        # if we get an error that means the user did not format our duration proprely
        except:
            
            # send our error message
            return await ctx.send("❌ **Please send a valid duration ex: `2h` `5d` `1m` ect...**")

        # set our valid units
        validUnits = ['s','m', 'h', 'd', 'w']

        # if our unit is not in the valid unit list
        if unit.lower() not in validUnits:

            # The user didnt format the duration proprely
            # send our error message
            return await ctx.send("❌ **Please send a valid duration ex: `2h` `5d` `1m` `8s`**")
        
        mutedur = None

        if unit.lower() == 's':

            mutedur = now + datetime.timedelta(seconds=time)
        
        elif unit.lower() == 'm':
            
            mutedur = now + datetime.timedelta(minutes=time)

        elif unit.lower() == 'h':
            
            mutedur = now + datetime.timedelta(hours=time)

        elif unit.lower() == 'd':

            mutedur = now + datetime.timedelta(days=time)

        elif unit.lower() == 'w':    

            mutedur = now + datetime.timedelta(weeks=time)
        
        maxhelpertime = now + datetime.timedelta(hours=2)

        if mutedur > maxhelpertime:

            if ctx.author.roles[-1].id == 556908650845962264:

                return await ctx.send("❌ **Helpers can mute for a maximum of 2 hours**")

        muterole = await self.client.fetch_mute_role(ctx.guild)
        await user.add_roles(muterole)
        self.client.mute(ctx.guild.id, user.id, ctx.author.id, reason, mutedur)

        emb = discord.Embed(title=f"✅ Mute successful", description=f'{user.mention} was muted for **`{h.precisedelta(mutedur)}`**', color=0xFCFCFC)
        emb.set_thumbnail(url=user.avatar_url)
        emb.add_field(name="Details", value=f"Muted by: {ctx.author.mention}\nReason: {reason}")
        await ctx.send(embed=emb)

        emb2 = discord.Embed(title=f"Muted!", description=f'You\'ve been muted in {ctx.guild} for, **`{h.precisedelta(mutedur)}`**', color=0xFCFCFC)
        emb2.add_field(name='Reason', value=reason)
        await user.send(embed=emb2)

    # mutelist command to list mutes
    @commands.check_any(commands.has_permissions(mute_members=True), commands.is_owner())
    @commands.command(name='mutelist', aliases=['mutes'], help='List all the mutes in the server.')
    async def _mutelist(self,ctx):

        # create a class for a user that left
        class userLeft():

            def __init__(self, id):

                self.id = id

                self.mention = f"<@!{id}>"

        # get all the mutes
        mutelist = self.client.fetch_mutes(ctx.guild.id)

        # create an embed
        emb = discord.Embed(title='Mutes', description=f"There are currently {len(mutelist)} active mutes.", color=0xFCFCFC)
        
        muteNumber = 1
        # add a field for ever mute
        for mute in mutelist:
            

            mod = get(ctx.guild.members, id=mute[4])
            usr = get(ctx.guild.members, id=mute[1])
            
            if usr is None:

                usr = userLeft(mute[0])
            
            if mod is None:

                mod = userLeft(mute[4])


            reason = mute[2]

            mtime = datetime.datetime.strptime(mute[3],'%Y-%m-%d %H:%M:%S.%f')

            emb.add_field(name=f'Mute #{muteNumber}', value=f"**User**: {usr.mention}\n**Reason**: {reason}\n**Moderator**: {mod.mention}\n**Time remaining**: {h.precisedelta(mtime)}")

            muteNumber += 1
        
        await ctx.send(embed=emb)

    # unmute command to unmute users in the server
    @commands.check_any(commands.has_permissions(manage_roles=True), commands.is_owner())
    @commands.command(name='unmute', aliases=['umute'], help='Unmute a user in the server.', usage='`[Userid or Mention]`')
    async def _unmute(self,ctx,user):
        
        # get the user from the input
        user = self.client.fetch_simple_member(ctx, user)

        # if the invokes top role is under the users top role
        if ctx.author.roles[-1].position < user.roles[-1].position:

            # the invoker does not have permission to mute the user
            emb = discord.Embed(title=f"{self.crossemoji} Member could not be unmuted!",colour=0xFCFCFC)
            emb.add_field(name="Error", value=f"``You don't have permission to do that!``")
            return await ctx.send(emb=emb)     

        muterole = await self.client.fetch_mute_role(ctx.guild)
        await user.remove_roles(muterole)
        self.client.unmute(ctx.guild.id, user.id)

        emb = discord.Embed(title=f"✅ Unmute successful", description=f'{user.mention} was unmuted', color=0xFCFCFC)
        emb.set_thumbnail(url=user.avatar_url)
        emb.add_field(name="Details", value=f"Unmuted by: {ctx.author.mention}")
        await ctx.send(embed=emb)

        emb2 = discord.Embed(title=f"Unmuted!", description=f'You\'ve been Unmuted in {ctx.guild}', color=0xFCFCFC)
        await user.send(embed=emb2)

    """
    # rules command to show the rules
    @commands.check_any(commands.check(has_helper), commands.check(check_channel))
    @commands.command(name='rules', aliases=['r', 'rule'], help='Fetch a rule from the #rules channel.', usage='`[Rule]`')
    async def _rules(self,ctx,rule):
        
        rule = str(float(rule))

        rule = rule.split('.')


        try:
            selected = self.ruledict[int(rule[0])][int(rule[1])]
        
    
            await ctx.send(f"**Rule {rule[0]}.{rule[1]}:**{selected}")

        except KeyError:

            await ctx.send("❌ **Selected rule not found!**")
    """

    # Purge command is to delete a large number of messages
    @commands.check_any(commands.has_permissions(manage_messages=True))
    @commands.command(name = 'purge',aliases=['clear','clr'], help='Clear a number of messages from the channel.', usage='`[Ammount]`')
    async def _purge(self,ctx,*args):

        # set the current channel as the channel variable
        channel = ctx.channel

        # set the aliases for the silent arg
        silent = ['-s', '--silent']
        
        # try and purge the channel
        try:
            # if the silent arg is present
            if args[0].lower() in silent:
                
                # try get the ammount we want to purge
                try:
                    purgeammount = int(args[1])
                
                # if the ammount is not there default to five
                except:

                    purgeammount = 5

                # try and purge the channel with the specified number of messages
                try:
                    
                    # purge the channel
                    await channel.purge(limit=purgeammount+1)

                # in the event of an exception
                except Exception as err:   

                    # send the error message
                    await ctx.send(f"Could not purge the channel: {err} ", delete_after=5.0)

            # if it isnt present
            else:

                # set the current channel as the channel variable
                channel = ctx.channel

                # get the ammount we want to purge
                purgeammount = int(args[0])
                
                # try and purge the channel with the specified number of messages
                try:
                    
                    # purge the channel
                    await channel.purge(limit=purgeammount+1)

                    # send feedback
                    await ctx.send(f"{self.checkemoji} Successfully purged ``{purgeammount}`` messages", delete_after=20)

                # in the event of an exception
                except Exception as err:   

                    # send the error message
                    await ctx.send(f"Could not purge the channel: {err} ", delete_after=5.0)

        # in the event of an exception the reason the user probably didnt specify a number of messages to purge
        except:

            # try and do this
            try:

                # purge 5 messages
                await channel.purge(limit=5+1)

                # send feedback
                await ctx.send(f"{self.checkemoji} Successfully purged ``5`` messages", delete_after=20)

            # in the event of an exception
            except Exception as err:

                # send the error message
                await ctx.send(f"Could not purge the channel: {err} ", delete_after=5.0)

        # PS: The reason we add 1 when we purge is because all this code is executed after the user invokes the command and so we want to delete everything before they invoke the command

    # hackban command is to ban a user before they even join the server
    @commands.check_any(commands.has_permissions(ban_members=True), commands.is_owner())
    @commands.command(name='hackban', help='Ban a user even though they arent in the server', usage='`[userid]`')
    async def _hackban(self,ctx,userid, *, reason='None Given'):

        # Try to Convert our input into an integer so all our datatypes match
        try:
            userid = int(userid)
            
        # if we get an error that measn theres letters in the input well tell the user to input a valid ID
        except:

            # print our error
            print(f"{self.crossemoji} **Please input a valid user ID to hackban**")


        # get all the hackbans 
        hbans = self.client.fetch_hackbans(ctx.guild.id)

        # get every hackabn and put the userids in a list
        hbans = [x[0] for x in hbans]

        if int(userid) in hbans:

            # create our feedback embed
            emb = discord.Embed(title=f"{self.crossemoji} User already hackbanned", description='You can\'t hackban someone thats already hackbanned', color=0xFCFCFC)

            # send our embed
            return await ctx.channel.send(embed=emb)           

        # request the user from the discord api
        req = request_discord_user(userid).text

        # convert the web request results to a json
        # the request returned would look like this {'id': '206250435848306692', 'username': 'Bicnu', 'avatar': '398c34f643240e91d2e2f34233d29745', 'discriminator': '5326', 'public_flags': 256}
        res = json.loads(req)

        # try and find the user in the guild
        usercheck = get(ctx.guild.members, id=int(userid))

        print(usercheck)
        # if the user is not in the guild continue
        if usercheck == None:

            pass
        
        # if the user is found
        else:

            # create our feedback embed
            emb = discord.Embed(title=f"{self.crossemoji} User is already in the server!", description='You can\'t hackban someone thats already in the server.', color=0xFCFCFC)
            emb.set_thumbnail(url=usercheck.avatar_url)
            # send our embed
            return await ctx.channel.send(embed=emb)


        # if user name is in the json keys that means that the user exists and we can ban them if they ever join the server
        if 'username' in res.keys():
        # continue with the hackbanning process 
            
            # add the userid to the hackban database for later processing
            self.client.hackban(ctx.guild.id, userid, reason)

            # create our feedback embed
            # REF: https://cdn.discordapp.com/avatars/206250435848306692/398c34f643240e91d2e2f34233d29745.png
            
            emb = discord.Embed(title=f"{res['username']}#{res['discriminator']}", description='User was successfully hackbanned!', color=0xFCFCFC)
            emb.set_thumbnail(url=f'https://cdn.discordapp.com/avatars/{userid}/{res["avatar"]}.png')
            emb.add_field(name='Reason', value=reason)

            await ctx.channel.send(embed=emb)


        # if username is not in the json keys that means the user does not exist   
        else:
        # stop it right there!

            emb = discord.Embed(title=f"{self.crossemoji} User not found!", description='I could not find that user in the discord API', color=0xFCFCFC)

            await ctx.channel.send(embed=emb)

    # hackban command is to ban a user before they even join the server
    @commands.check_any(commands.has_permissions(ban_members=True), commands.is_owner())
    @commands.command(name='unhackban', help='unhackban a user', usage='`[userid]`')
    async def _unhackban(self,ctx,userid):

        # Try to Convert our input into an integer so all our datatypes match
        try:
            userid = int(userid)
            
        # if we get an error that measn theres letters in the input well tell the user to input a valid ID
        except:

            # print our error
            print(f"{self.crossemoji} Please input a valid user ID to unhackban")

        # get all the hackbans 
        hbans = self.client.fetch_hackbans(ctx.guild.id)

        # get every hackabn and put the userids in a list
        hbans = [x[1] for x in hbans]

        if int(userid) not in hbans:

            # create our feedback embed
            emb = discord.Embed(title=f"{self.crossemoji} User isnt hackbanned", description='You can\'t unhackban someone thats not already hackbanned', color=0xFCFCFC)

            # send our embed
            return await ctx.channel.send(embed=emb)           

        # request the user from the discord api
        req = request_discord_user(userid).text

        # convert the web request results to a json
        # the request returned would look like this {'id': '206250435848306692', 'username': 'Bicnu', 'avatar': '398c34f643240e91d2e2f34233d29745', 'discriminator': '5326', 'public_flags': 256}
        res = json.loads(req)

        # try and find the user in the guild
        usercheck = get(ctx.guild.members, id=userid)

        # if the user is not in the guild continue
        if usercheck == None:
            pass
        
        # if the user is found
        else:

            # create our feedback embed
            emb = discord.Embed(title=f"{self.crossemoji} User is already in the server!", description='You can\'t hackban someone thats already in the server.', color=0xFCFCFC)

            # send our embed
            return await ctx.channel.send(embed=emb)


        # if user name is in the json keys that means that the user exists and we can ban them if they ever join the server
        if 'username' in res.keys():
        # continue with the unhackbanning process 
            
            # remove the userid from the hackban database
            self.client.unhackban(ctx.guild.id, userid)

            emb = discord.Embed(title=f"{res['username']}#{res['discriminator']}", description='User successfully unhackbanned', color=0xFCFCFC)
            emb.set_thumbnail(url=f'https://cdn.discordapp.com/avatars/{userid}/{res["avatar"]}.png')

            await ctx.channel.send(embed=emb)

        # if username is not in the json keys that means the user does not exist   
        else:
        # stop it right there!

            emb = discord.Embed(title=f"{self.crossemoji} User not found!", description='I could not find that user in the discord API', color=0xFCFCFC)

            await ctx.channel.send(embed=emb)

    # Banlist command is to fetch all the bans
    @commands.check_any(commands.is_owner(), commands.has_permissions(ban_members=True))
    @commands.command(name='banlist',aliases=['bans'], help='List all the banned users in the guild')
    async def _banlist(self,ctx):

        # get all the guild bans
        banlist = await ctx.guild.bans()

        # initialize the bans list array
        bans = []

        # add all the guild bans to the ban list array
        for ban in banlist:
            bans.append(ban)

        # initialize the embed
        pageNums = int(len(bans)/25) + 1

        # get the ammount of bans per embed page
        bansperpage = int(len(bans)/pageNums)

        # set the ammount of pages as an array so we can loop through it and run some code for every page
        i = list(range(0, pageNums))

        # initialize the embeds array
        embeds = []

        # for every page we need
        for x in i:

            # make an embed for the page
            emb = discord.Embed(title=f"All guild bans page {x+1}", color=discord.Color.dark_red())
            emb.set_thumbnail(url=ctx.guild.icon_url)

            # add that to the embeds array
            embeds.append(emb)

        # ammount of bans on the page we have currently selected
        bansammount = 0

        # what page we are on to index the right embed
        page = 0

        # for every guiold the bot is in
        for ban in bans:

            # if the bans on the current page reaches  the maximum
            if bansammount >= bansperpage:

                # change to the next page and set the bans ammount on that page to 0
                bansammount = 0
                page += 1
            
            # select the correct page we are on
            emb = embeds[page]  

            # add a ban to the page
            emb.add_field(name=f"{ban[1]} - {ban[1].id}", value = f"{ban[0]}", inline=False)
            
            # add one to the bansammount  variable so when it hits the max per page the page can chage
            bansammount += 1

        # send the initial embed
        msg = await ctx.send(embed = embeds[0])

        # add the reaction menu
        await msg.add_reaction('◀')
        await msg.add_reaction('⏹')
        await msg.add_reaction('▶')

        # current page that we are on
        currentpage=0

        # number of times we have used the menu
        uses = 0

        # the check function is for when we are waiting for a reaction from the user
        def check(reaction, user):
            # over here we are checking if the user that added the reaction is the same user that invoked the dev guilds command
            return reaction.message.id == msg.id and user == ctx.author

        # while weve used the menu less than 15 times
        while uses < 15:
            # try this...
            try:

                # await a reaction
                reaction, _ = await self.client.wait_for('reaction_add', timeout=100.0, check=check)

                # try and remove the reaction
                try:
                    await msg.remove_reaction(reaction.emoji, ctx.author)
                
                # in the event of an excepton ... 
                except:
                    # just continue...
                    pass

                # if the page is less than then the max pages and our reaction is next
                if reaction.emoji == '▶' and page < pageNums:

                    # increment what page we are on and our uses
                    page +=1
                    uses +=1

                    # edit the embed
                    await msg.edit(embed=embeds[currentpage])

                # if the page is less than the max pages or equal to the max pages and our reaction is back
                if reaction.emoji == '◀' and page <= pageNums:
                    
                    # if the page is 0 
                    if page == 0:
                        # do nothing
                        pass
                    
                    # if the page is anything other than 0 
                    else:

                        # decrement what page we are on and increment our uses
                        page -=1
                        uses +=1

                    # edit the embed
                    await msg.edit(embed=embeds[currentpage])

                # if the reaction is stop
                if reaction.emoji == '⏹':

                    # delete the message
                    await msg.delete()

            # after the 60 second timeout on the reaction wait event
            except TimeoutError:

                # set the uses to 15
                uses = 15                

    # -----------------ERROR HANDLERS-----------------------------------
    # For every command we also have an error handler. These methods are run when the Check_any decorator fails and returns an error.
    # This also allows us to have code that runs only when a specific error is raised Without having to have too many try: except: 's

    # purge error handler
    @_purge.error
    async def _purge_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

             # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")
        
        # if the error is any other instance just print the error
        else:

            print(error)

    # ban error handler
    @_ban.error
    async def _ban_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

            # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")
        
        # if the error is any other instance just print the error
        else:

            print(error)

    # unban error handler
    @_unban.error
    async def _unban_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

            # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")
        
        # if the error is any other instance just print the error
        else:

            print(error)
    
    # banlist error handler
    @_banlist.error
    async def _banlist_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

            # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")
        
        # if the error is any other instance just print the error
        else:

            print(error)
    
    # kick error handler
    @_kick.error
    async def _kick_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

            # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")
        
        # if the error is any other instance just print the error
        else:

            print(error)
        

    # ban error handler
    @_hackban.error
    async def _hackban_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

            # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")
        
        # if the error is any other instance just print the error
        else:

            print(error)

    # unban error handler
    @_unhackban.error
    async def _unhackban_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

            # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")
        
        # if the error is any other instance just print the error
        else:

            print(error)
    
    # config error handler
    @_config.error
    async def _config_handler(self,ctx,error):

        # if the error is an instance of CheckAnyFailure It means the user didnt pass the checks before running the command. This means the user is not on the owner list or doesnt have the suffecient permissions to use the command
        if isinstance(error,commands.CheckAnyFailure):

            # send the error message
            await ctx.send(f"{self.crossemoji} **You don't have permission to use this command!**")

        # if the error is any other instance just print the error
        else:

            print(error)
    

def setup(client):  
    client.add_cog(moderation(client))