# import the necessary packages
from io import BytesIO

import datetime
import discord
import humanize as h
import requests
import time
from discord.ext import commands

from client import Client


# define the subclassed Help command
class helpCommand(commands.MinimalHelpCommand):
    """This is an example of a HelpCommand that utilizes embeds.
    It's pretty basic but it lacks some nuances that people might expect.
    1. It breaks if you have more than 25 cogs or more than 25 subcommands. (Most people don't reach this)
    2. It doesn't DM users. To do this, you have to override `get_destination`. It's simple.
    Other than those two things this is a basic skeleton to get you started. It should
    be simple to modify if you desire some other behaviour.
    
    To use this, pass it to the bot constructor e.g.:
    
    bot = commands.Bot(help_command=EmbedHelpCommand())
    """
    # Set the embed colour here
    COLOUR = discord.Colour.blurple()

    def get_ending_note(self):
        return 'Use {0}{1} [command] for more info on a command.'.format(self.clean_prefix, self.invoked_with)

    def get_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_bot_help(self, mapping):
        self.COLOUR = 0x2F3136
        embed = discord.Embed(title='Bot Commands', colour=self.COLOUR)
        description = self.context.bot.description
        if description:
            embed.description = description

        for cog, cmds in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name.capitalize()
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                value = '\u2002'.join("`" + c.name + '`' for c in cmds)
                if cog and cog.description:
                    value = '{0}\n{1}'.format(cog.description, value)

                if name != 'Jishaku':
                    embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        self.COLOUR = 0x2F3136
        embed = discord.Embed(title=f'{cog.qualified_name.capitalize()} Commands', colour=self.COLOUR)
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...', inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        self.COLOUR = 0x2F3136
        embed = discord.Embed(title=group.qualified_name, colour=self.COLOUR)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...',
                                inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):

        embed = discord.Embed(title=f"{self.get_command_signature(command)}", description=command.short_doc,
                              colour=0x2F3136)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)


# define the sniped message class
class snipedMessage:

    # init code
    def __init__(self, message):
        # set the message content as a self variable
        self.content = message.content

        # set the message author as a self variable
        self.author = message.author

        # set the message channel as a self variable
        self.channel = message.channel

        # set the message created timestamp as a self variable
        self.created_at = message.created_at

        # set the Current time as the deleted_at self variable (We do this beacuase we will only create an instance
        # of this class once a message is deleted. Which means we can track when the message was deleted.)
        self.deleted_at = datetime.datetime.now()

        # set the message attachments as a self variable
        self.attachments = message.attachments

    # repr code
    def __repr__(self):
        # return what you want the class to return when no self proprety is selected
        return f'<snipedMessage Instance, ' \
               f'author={str(self.author)} ' \
               f'channel={str(self.channel)} ' \
               f'deleted_at={self.deleted_at}>'


# define the cog class
class utility(commands.Cog):
    """
    Commands for general use.
    """

    # init code
    def __init__(self, client):

        # set the global client variable
        self.client: Client = client

        # set the global "sniped" dict variable. This will be needed to store our sniped messages in the snipe command
        self.sniped = {}

        # get the original help command of the bot
        self.defaultHelpCommand = client.help_command

        # get the new subclasseed help command
        self.newHelpCommand = helpCommand()

        # set the client help command to the new subclassed help command
        client.help_command = self.newHelpCommand

        # set the cog of the help command to this one
        client.help_command.cog = self

    # this method is called when the Cog is unloaded
    def cog_unload(self):

        # set the client help command back to the original one
        self.client.help_command = self.defaultHelpCommand

    # on_message_delete event listener for our snipe command
    @commands.Cog.listener()
    async def on_message_delete(self, message):

        # set the channel id key in the sniped dict as a new instance of snopedMessage
        self.sniped[message.channel.id] = snipedMessage(message)

    # snipe command is to fetch the last deleted message
    @commands.command(name='snipe', aliases=['snp'], help="Fetch the last deleted message from the channel.")
    async def _snipe(self, ctx):

        # try and get the current sniped message for this channnel
        try:

            # set the sniped command as the "sniped" variable
            sniped: snipedMessage = self.sniped[ctx.channel.id]

            # create the embed 
            emb = discord.Embed(title=f'🔫 SNIPED MESSAGE',
                                description=f'{sniped.content}',
                                color=0x2F3136)

            # add the field with the time send
            emb.add_field(name="Time deleted", value=h.naturaltime(sniped.deleted_at))

            # add the message author to the field
            emb.add_field(name='Author', value=sniped.author.mention)

            # add the user avatar url as the thumbnail
            emb.set_thumbnail(url=sniped.author.avatar_url)

            # check if the message attachments are available
            # try and set the image to the attachment
            try:

                # get the attachment
                img = sniped.attachments[0]

                # add it to the embed
                emb.set_image(url=img.proxy_url)

            # if we get an error that means the image is no longer availible
            except Exception:

                # do nothing
                pass

            # send the embed
            await ctx.send(embed=emb)

        # if we get a KeyError that means the key doesnt exist which means theres no sniped message
        except KeyError:

            return await ctx.send("``Could not find a sniped message``")

    # bot info command is to fetch info about the bot
    @commands.command(name='botinfo', aliases=['stats', 'binfo', 'about'], help="Get information about the bot.")
    async def _botinfo(self, ctx):

        # get the server count of the bot
        serverCount = len(self.client.guilds)

        # get the user count of the bot we turn the get all members method to a set so it doesnt repeat any members
        # that could be in more than 1 server.
        userCount = len(set(self.client.get_all_members()))

        # create the embed to send and add all the fields for the previos variables
        emb = discord.Embed(title=f'{self.client.user.name} Stats',
                            timestamp=datetime.datetime.utcnow())

        emb.add_field(name='Client Version',
                      value=self.client.version,
                      inline=True)

        emb.add_field(name='Python Version',
                      value=self.client.pyversion,
                      inline=True)

        emb.add_field(name='Discord.py Version',
                      value=self.client.dpyversion,
                      inline=True)

        emb.add_field(name='Total Guilds',
                      value=serverCount,
                      inline=True)

        emb.add_field(name='Total Users',
                      value=userCount,
                      inline=True)

        # add the current prefix to the embed
        emb.add_field(name="Client Uptime",
                      value=f"{h.naturaldelta(self.client.start_time)}")

        # add the client owner to the embed
        emb.add_field(name='Bot Creator',
                      value=f"<@393165866285662208>")

        # add the footer to the command
        emb.set_footer(text=f'{self.client.user.name} | Command credit: Tayso20')

        # set the thumbnail to the client profile photo
        emb.set_thumbnail(url=self.client.user.avatar_url)

        # add a github field to the embed
        emb.add_field(name='Github Page',
                      value='[github.com/...](https://github.com/BlutopiaHub/Blutonium-2.0)',
                      inline=True)

        # add the bot invite link to the embed
        emb.add_field(name='Invite Link',
                      value=f'[discord.com/...](https://discord.com/oauth2/authorize?client_id=' +
                            f'{self.client.user.id}&scope=bot&permissions=8)')

        # send the embed
        await ctx.send(embed=emb)

    # uptime command is to get the bot uptime and extension uptimes
    @commands.command(name='uptime', aliases=['ut'],
                      help="Get the uptime of the client and the extensions that are loaded.")
    async def _uptime(self, ctx):

        # get the extension cache
        exts = self.client.ext_cache

        # create the embed
        emb = discord.Embed(title='Uptime',
                            description=f"The client has been running for **{h.precisedelta(self.client.start_time)}**",
                            timestamp=datetime.datetime.utcnow())

        # for every extension loaded
        for ext in self.client.extensions:

            # try and add it to the embed
            try:
                # add the extension name as well as how long ago it was loaded (from the cache)
                emb.add_field(name=ext.split('.')[2].capitalize(),
                              value=f'Loaded **{h.naturaltime(exts[ext]["start_time"])}**' +
                                    f'\n**{ext.split(".")[1].capitalize()}** extension\n\_\_\_\_\_\_\_\_',
                              inline=True)

            # if we get an error it means the loaded extension is not cached
            except KeyError:

                # we will just ignore this error
                pass

        # send the embed 
        await ctx.send(embed=emb)

    # ping command is to get the bot, ws, and db ping
    @commands.command(name='ping', aliases=['pong'],
                      help="Get the latencey for the bot messages, websocket, and database.")
    async def _ping(self, ctx):

        # get the current time
        bf = time.monotonic()

        # send a message
        msg = await ctx.send("...")

        # subtract the before time from the now time to get the ping
        pong = (time.monotonic() - bf) * 1000

        # get the current time
        bf = time.monotonic()

        # make a db query
        self.client.db.run("SELECT * FROM guilddata")

        # subtract the before time from the now time to get the ping 
        peng = (time.monotonic() - bf) * 1000

        # get the ws latency
        ping = round(self.client.latency * 1000, 1)
        pong = round(pong, 1)
        peng = round(peng, 1)

        # create the embed
        emb = discord.Embed(title='⏳Ping',
                            description=f'🌐 Websocket Latency: `{ping} ms`\n💬 Message Latency: `{pong} ms`\n🐘 ' +
                                        f'Database Latency: `{peng} ms`',
                            color=0x2F3136)

        # send the client latency
        await msg.edit(embed=emb, content='\u2002')

    # userinfo command is to get information on a user and display it
    @commands.command(name='userinfo', aliases=['ui', 'uinfo', 'profile', 'whois', ''])
    async def _userinfo(self, ctx, *, user=None):

        # try and get the user using the input given
        user: discord.Member = self.client.fetch_member(ctx, user)

        # for our first peice of user info were gonna get the permissions that the user has in the guild
        # first we make a list named perms, this will contain all the permissions that we want to display.
        perms = []

        # for every permission that the user has in the guild
        for perm in user.guild_permissions:

            # make a list of permissions that we want to be displayed if the user has them
            key = ['ban members', 'kick members', 'manage messages', 'manage guild', 'mention everyone',
                   'administrator', 'send messages']

            # the guild_permissions item includes every permission in a tuple with wether the permission is allowed
            # if the second object in the tuple is True that means the permission is allwed for the user
            if perm[1]:

                # get the name of the permission
                name = perm[0]

                # permission names by defauly are formatted like "Manage_Messages" we want to remove the underscore
                # and add a space instead replace the underscore by a space
                name = name.replace('_', ' ')

                # if the name is in the list of permissions that we want to display
                if name in key:

                    # add the name to the list that contains all the permissions we want to display
                    perms.append(f'{name}\n')

                # if the name is not in the list of permisssions we want to display
                else:

                    # just continue
                    pass

        # make a method called checkfornitro. This checks if the user's avatar is animated and also checks if the
        # user has a nitro booster role

    # invite command is to get the invite link for the bot and support server
    @commands.command(name='invite', aliases=['inv', 'support'],
                      help='Gets the invite link to the bot and the support server for blutonium.')
    async def _invite(self, ctx):

        # create our embed that we will send to the user
        emb = discord.Embed(title=f'Invite {self.client.user}', timestamp=datetime.datetime.utcnow(), colour=0x2F3136,
                            description=f'[Invite me to your server!](https://discordapp.com/oauth2/authorize?' +
                                        f'client_id={self.client.user.id}&scope=bot&permissions=8)\n' +
                                        f'[Join the Blutonium updates and support server.](https://discord.gg/NNfD6eQ)')

        # add a thumbnail to our embed
        emb.set_thumbnail(url=self.client.user.avatar_url)

        # send our embed
        await ctx.send(embed=emb)

    # servericon command is to fetch the icon of the guild
    @commands.command(name='servericon', aliases=['sicon', 'sic'], help='Fetch the icon of the current guild.')
    async def _servericon(self, ctx):

        # request the server icon
        pull = requests.get(ctx.guild.icon_url)

        # turn the request into an image
        image = BytesIO(pull.content)

        # if the guild has an animated icon URL
        if ctx.guild.is_icon_animated:

            # name the file after the guild and make sure its in the GIF format
            image.name = f"{ctx.guild}.gif"

        # if it doenst
        else:

            # name the file after the guild and make sure its in the PNG format
            image.name = f"{ctx.guild}.png"

        # turn the image in to a discord.File instance
        file = discord.File(image)

        # send the file
        await ctx.send(file=file)


# setup function is called when the client loads the extension
def setup(client):
    cog = utility(client)

    client.add_cog(cog)
