# import the necessary packages
import discord, os, datetime
from discord.ext import commands
from setup import  OWNERID
import humanize as h
from discord.utils import get

# guild embed method
def guildembed(guild):

    # initialize the embed
    embed = discord.Embed(title = f'{guild}',colour = discord.Colour.blue(),timestamp=datetime.datetime.now())

    # initialize the bot count
    botcount = 0
    
    # for every user in guild members
    for bot in guild.members:
        # if the user is a bot
        if bot.bot:
            # increment botcount by 1
            botcount += 1

    # normal users is all the users - the bots        
    membercount = len(guild.members) - botcount

    # get the number of text channels
    TextChs = len(guild.text_channels)

    # Count all the voice channels
    voiceChs = len(guild.voice_channels)

    # Count all the categories
    catcount = len(guild.categories)

    # Count all the roles
    roles = len(guild.roles)

    # get the guild icon url
    servericonurl = str(guild.icon_url)

    # set the embed text channel field
    embed.add_field(name='Text channels',value=TextChs,inline=True)

    # set the embed categories field
    embed.add_field(name='categories',value=catcount,inline=True)

    # Set the embed region field
    embed.add_field(name='Region',value=f'{guild.region}',inline=True)
    
    # Set the embed voice channels field
    embed.add_field(name='Voice channels',value=voiceChs,inline=True)

    # Set the server id field
    embed.add_field(name='Server ID',value=f'{guild.id}',inline=True)
    
    # Set the server owner field
    embed.add_field(name='Server owner', value=f'{guild.owner}',inline=True)

    # Set the total members field
    embed.add_field(name='total members',value=len(guild.members),inline=True)

    # Set the total humans field
    embed.add_field(name='humans', value=membercount,inline=True)

    # Set the total bots field
    embed.add_field(name='bots',value=botcount,inline=True)

    # Set the guild created field
    embed.add_field(name='Created',value=f'{h.naturaltime(guild.created_at)}',inline=True)

    # Set the roles field
    embed.add_field(name='roles',value=roles)

    # Set the embed thumbnail
    embed.set_thumbnail(url=servericonurl)

    # return the whole embed
    return embed    

# define the cog class
class owner(commands.Cog, name='Owner'):

    # init code
    def __init__(self,client):

        self.client = client
        self.lastmessage = {}

    # dev top command
    @commands.is_owner()
    @commands.group(name='developer', aliases=['dev', 'devtools'], help="Commands only used by high level individuals")
    async def _developer(self,ctx:commands.Context):

        # the dev command is a set of commands used to do things only meant for the client owners.

        if ctx.invoked_subcommand is None:
            return

    # dev -> temp subcommand
    @_developer.command(name='temp', aliases=['mkcmd', 'addcmd'], help="Write some quick code inside discord!")
    async def _tempCmd(self,ctx, filename, *,cmd):

        cmd = cmd.strip('```')
        
        with open(f'extensions/temp/{filename}.py', 'w') as text_file:

            text_file.write(cmd)

    # dev -> blacklist command group
    @_developer.group(name='blacklist', aliases=['bl'], help="Blacklist or unblacklist a user.")
    async def _blacklist(self,ctx):

        # the blacklist command group is a group of commands for adding and removing users from the blacklist.
        
        # if theres no subcommand that is invoked
        if ctx.invoked_subcommand is None:

            # were going to list the blacklist 
            
            # get the blacklist
            blacklist = set(self.client.blacklist_cache)

            # make an embed for all the blacklisted users
            emb = discord.Embed(title='Blacklisted Users', description=f'{len(blacklist)} Blacklisted Users')

            # for ever id in the blacklist
            for id in blacklist:

                # get the user from the ID
                user = get(self.client.get_all_members(), id=id)

                # if the user is None that means that the user could not be found
                if user is None:
                    # skip all
                    pass
                
                # if the user has a value 
                else:

                    # add the user to the embed
                    emb.add_field(name=f'{user.name}', value=f"ID: {user.id}\nTag: {user.discriminator}")
            
            # send the embed!
            await ctx.send(embed=emb)

    # dev -> blacklist -> remove subcommand
    @_blacklist.command(name='remove', aliases=['delete','rem'], help="Remove a user from the blacklist")
    async def _blacklistRem(self,ctx, id:int):

        # try and fetch the user through the ID
        user = get(self.client.get_all_members(), id=id)

        # if the user variable is None that means the client could not find a user with that ID
        if user is None:

            return await  ctx.send("Could not find that user!")
        
        # get the user blacklist
        blacklist = self.client.blacklist_cache

        # if the user is not already blacklisted we dont need to unblacklist
        if user.id not in blacklist:

            return await ctx.send("User is not blacklisted")

        # if the user is blacklisted then we should blacklist the user
        else:
            
            # remeve the users id from the blacklist
            self.client.unblacklist(user.id)

            # send the feedback message
            await ctx.send(f"User **{user}** was successfully unblacklisted")

    # dev -> blacklist -> add subcommand
    @_blacklist.command(name='add', aliases=['append'], help="Add a user to the blacklist")
    async def _blacklistAdd(self,ctx, id:int):

        # try and fetch the user through the ID
        user = get(self.client.get_all_members(), id=id)

        # if the user variable is None that means the client could not find a user with that ID
        if user is None:

            return await  ctx.send("Could not find that user!")
        
        # get the user blacklist
        blacklist = self.client.blacklist_cache

        # if the user is already blacklisted we dont need to blacklist them again.
        if user.id in blacklist:

            return await ctx.send("User is already blacklisted")

        # if the user is not blacklisted then we should blacklist the user
        else:
            
            # add the users id to the blacklist
            self.client.blacklist(user.id)

            # send the feedback message
            await ctx.send(f"User **{user}** was successfully blacklisted")

    # dev -> sql subcommand
    @_developer.command(name='sql', aliases=['pg', 'pgsql', 'postgres'], help='Run SQL queries and statments in discord!')
    async def _sql(self,ctx,*args):

        
        # define the full query string
        sql = " ".join(args)

        # send the sql query
        result = self.client.db.run(sql)

        # send the feedback
        await ctx.send(f"**{result}**")

    # dev -> say subcommand
    @_developer.command(name='say', aliases=['send'], help="Send a message as the bot")
    async def _say(self,ctx,*args):

    
        # get the users message
        original = ctx.message

        # if the silent arg is present...
        if args[0] == '-s':

            try:
                # delete the users message
                await original.delete()

                # remove the slient arg from the rest of the args
                args = args[1:]
            except:
                pass
        
        # set the rest of the args as the message content
        message = " ".join(args)

        # send the message as well as set it as the last message variable for our editing subcommand
        self.lastmessage[ctx.guild.id] = await ctx.send(message)

    # dev -> edit subcommand
    @_developer.command(name='edit', aliases=['ed'], help="Edit the last sent message from the bot using the dev/say command")
    async def _edit(self,ctx,*args):

    
        # get the users message
        original = ctx.message

        # get the last send message
        editor = self.lastmessage[ctx.guild.id]

        # if the silent arg is present...
        if args[0] == '-s':

            try:
                # delete the users message
                await original.delete()

                # remove the slient arg from the rest of the args 
                args = args[1:]
            except:            
                pass

        # set the rest of the args as the message content
        message = " ".join(args)

        # edit the last message
        await editor.edit(content=message)

    # dev -> prefix subcommand
    @_developer.command(name='prefix', aliases=['setprefix', 'pre'], help="Set the guild prefix")
    async def _prefix(self,ctx,*args):
        
        # get previous prefix
        previous = self.client.fetch_prefix(ctx.guild.id)

        # get the new prefix from input
        new = args[0]

        # update the guild prefix
        update = self.client.update_prefix(ctx.guild.id,new)

        # Create the feedback embed
        emb = discord.Embed(title=f'{ctx.guild}', description='The prefix for this guild was changed!', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())

        # Add the fields which illustrate the prefix change
        emb.add_field(name='Previous prefix', value=f'{previous}')
        emb.add_field(name='New prefix', value=f'{new}')

        # send the embed 
        await ctx.channel.send(embed=emb)

    # dev -> guilds subcommand
    @_developer.command(name='guilds', aliases=['g','servers'], help="Fetch all the guilds that the client can see")
    async def _guilds(self,ctx,*args):
        # get all the guilds
        allguilds = self.client.guilds       
        
        try:
            id = int(args[0])
            guild = get(allguilds, id=id)
        except:
            id = " ".join(args)
            guild = get(allguilds, name=id)

        if guild is None:
            pass
        else:

            guild = guildembed(guild)

            return await ctx.send(embed=guild)

        # calculate all the pages needed
        pageNums = int(len(allguilds)/25) + 1
        
        # get the ammount of guilds per page
        guildsperpage = int(len(allguilds)/pageNums)
        
        # set the ammount of pages as a array to loop through
        i = list(range(0,pageNums))

        # initialize embeds array
        embeds = []

        # for each page in pages array
        for x in i:
            
            # make a new page embed
            emb = discord.Embed(title=f"All Guilds page {x+1}")

            # add that embed to the embeds array
            embeds.append(emb)
        

        # ammount of guilds added to the embed
        guilds = 0

        # what page we are on to index the right embed in emebds array
        page = 0 

        # for every guild the bot is in
        for guild in allguilds:
            
            # if the ammount of guilds in the embed is greater than or equal to the max guilds per page
            if guilds >= guildsperpage:

                # change to the next page and set the embeds on that page back to 0
                guilds = 0
                page += 1

            # select the right embed
            emb = embeds[page]

            # add a guild to that embed
            emb.add_field(name=guild,value=f"{len(guild.members)} Members - {guild.id}")

            # add 1 to the guilds variable so when the variable hits max guilds it switches pages
            guilds +=1

        # send the first page
        msg = await ctx.send(embed=embeds[0])

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

    # blacklist add error handler
    @_blacklistAdd.error
    async def _blacklistAdd_handler(self,ctx,error):


        if isinstance(error,commands.errors.BadArgument):

            await ctx.send("Please input a valid ID")

    # blacklist add error handler
    @_blacklistRem.error
    async def _blacklistRem_handler(self,ctx,error):


        if isinstance(error,commands.errors.BadArgument):

            await ctx.send("Please input a valid ID")

# setup function is called when the client loads the extension
def setup(client):

    cog = owner(client)
    client.add_cog(cog)
