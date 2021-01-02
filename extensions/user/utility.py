# import the necessary packages
from io import BytesIO

import datetime
import base64
import discord
import humanize as h
import requests
import time

from discord.ext import commands
from discord.utils import get
from discord import Spotify

from blutopia import Client, setup as s
from blutopia.utils import checkfornitro, chop_microseconds, request_song_info, find_joinpos, snipedMessage


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

        # initialize our global emote variables
        self.support = ''
        self.checkemoji = ''
        self.crossemoji = ''
        self.dashemoji = ''
        self.blutonium = ''

        # create the task for getting the emojis
        client.loop.create_task(self.getEmojis())

    # Define our class methods that will be used only by our class
    # We need this getemojis method to be a seperate method so we can use async since __init__ is not a coroutine
    async def getEmojis(self):

        # wait unitl the client is ready
        await self.client.wait_until_ready()

        # support server to get the emojis
        self.support = get(self.client.guilds, name="Blutonium updates and support", id=629436501964619776,
                           owner_id=393165866285662208)

        # Check emoji
        self.checkemoji = get(self.support.emojis, name="BlutoCheck")

        # X emoji
        self.crossemoji = get(self.support.emojis, name="BlutoX")

        # logo emoji
        self.blutonium = get(self.support.emojis, name="Blutonium")

        # dash emoji
        self.dashemoji = get(self.support.emojis, name='purple_dash')

    # Override the method that is called when the Cog is unloaded
    def cog_unload(self):

        # set the client help command back to the original one
        self.client.help_command = self.defaultHelpCommand

    # Define all of our commands
    # group of commands to fetch data about minecraft
    @commands.group(name='minecraft', aliases=['mc'],
                    head='Fetch minecraft data from lots of sources.')
    async def _minecraft(self, ctx):

        # if theres no invoked subcommand
        if ctx.invoked_subcommand is None:
            # get the guild prefix
            prefix = self.client.fetch_prefix(ctx.guild.id)

            # send the error message
            await ctx.send(f"{self.crossemoji}**Please Choose a valid subcommand! Use"
                           f"``{prefix}help minecraft`` so see a list of subcommands**")

    # Minecraft 2d head command
    @_minecraft.command(name='avatar', aliases=['av', '2dhead'],
                        help='Get a 2d view of a user\'s minecraft head')
    async def _minecraft_avatar(self, ctx, query, *args):

        # define or base url for our api request
        url = f'https://mc-heads.net/avatar/{query}'

        # add our args to the request url if any are present

        # if the --size arg is present
        if '--size' in args:

            # get the index of our size args so we can get the actual size that the user inputted
            argindex = args.index('--size')

            # add one to the arg index to get the size index
            sizeindex = argindex + 1

            # get the size that the user specifiend
            size = args[sizeindex]

            # try and convert the size to an int, if the size cant be converted to an int
            # that means the user didnt input a valid number
            try:

                # convert size to int
                size = int(size)

            # if we get a ValueError
            except ValueError:

                # send an error message
                return await ctx.send(f'{self.crossemoji}**Please input a valid number for the ``--size`` arg**')

            url += f'/{size}'

        # if the nohelm arg is present
        if '--nohelm' in args:
            # add /nohelm to the url
            url += '/nohelm'

        # request the file
        request = BytesIO(requests.get(url).content)

        # change the filename
        request.name = f'{query}.png'

        # Create the file
        file = discord.File(request)

        # send the file
        await ctx.send(file=file)

    # Minecraft 2d body command
    @_minecraft.command(name='player', aliases=['pl', '2dbody'],
                        help='Get a 2d view of a user\'s minecraft body')
    async def _minecraft_player(self, ctx, query, *args):

        # define or base url for our api request
        url = f'https://mc-heads.net/player/{query}'

        # add our args to the request url if any are present

        # if the --size arg is present
        if '--size' in args:

            # get the index of our size args so we can get the actual size that the user inputted
            argindex = args.index('--size')

            # add one to the arg index to get the size index
            sizeindex = argindex + 1

            # get the size that the user specifiend
            size = args[sizeindex]

            # try and convert the size to an int, if the size cant be converted to an int
            # that means the user didnt input a valid number
            try:

                # convert size to int
                size = int(size)

            # if we get a ValueError
            except ValueError:

                # send an error message
                return await ctx.send(f'{self.crossemoji}**Please input a valid number for the ``--size`` arg**')

            url += f'/{size}'

        # if the nohelm arg is present
        if '--nohelm' in args:
            # add /nohelm to the url
            url += '/nohelm'

        # request the file
        request = BytesIO(requests.get(url).content)

        # change the filename
        request.name = f'{query}.png'

        # Create the file
        file = discord.File(request)

        # send the file
        await ctx.send(file=file)

    # Minecraft 3d head command
    @_minecraft.command(name='head', aliases=['3dhead'],
                        help='Get a 3d view of a user\'s minecraft head')
    async def _minecraft_head(self, ctx, query, *args):

        # define or base url for our api request
        url = f'https://mc-heads.net/head/{query}'

        # add our args to the request url if any are present

        # if the --size arg is present
        if '--size' in args:

            # get the index of our size args so we can get the actual size that the user inputted
            argindex = args.index('--size')

            # add one to the arg index to get the size index
            sizeindex = argindex + 1

            # get the size that the user specifiend
            size = args[sizeindex]

            # try and convert the size to an int, if the size cant be converted to an int
            # that means the user didnt input a valid number
            try:

                # convert size to int
                size = int(size)

            # if we get a ValueError
            except ValueError:

                # send an error message
                return await ctx.send(f'{self.crossemoji}**Please input a valid number for the ``--size`` arg**')

            url += f'/{size}'

        # if the --nohelm arg is present
        if '--nohelm' in args:
            # add /nohelm to the url
            url += '/nohelm'

        # since we want --left and --right to be mutually exclusive,
        # we put them both in a while loop that breaks once one is added
        while True:

            # if the --left arg is present
            if '--left' in args:

                # add /left to the url
                url += '/left'
                break

            # if the --right arg is present
            elif '--right' in args:

                # add /right to the url
                url += '/right'
                break

            else:

                break

        # request the file
        request = BytesIO(requests.get(url).content)

        # change the filename
        request.name = f'{query}.png'

        # Create the file
        file = discord.File(request)

        print(url)

        # send the file
        await ctx.send(file=file)

    # Minecraft 3d body command
    @_minecraft.command(name='body', aliases=['3dbody', 'bod'],
                        help='Get a 3d view of a user\'s minecraft body')
    async def _minecraft_body(self, ctx, query, *args):

        # define or base url for our api request
        url = f'https://mc-heads.net/body/{query}'

        # add our args to the request url if any are present

        # if the --size arg is present
        if '--size' in args:

            # get the index of our size args so we can get the actual size that the user inputted
            argindex = args.index('--size')

            # add one to the arg index to get the size index
            sizeindex = argindex + 1

            # get the size that the user specifiend
            size = args[sizeindex]

            # try and convert the size to an int, if the size cant be converted to an int
            # that means the user didnt input a valid number
            try:

                # convert size to int
                size = int(size)

            # if we get a ValueError
            except ValueError:

                # send an error message
                return await ctx.send(f'{self.crossemoji}**Please input a valid number for the ``--size`` arg**')

            url += f'/{size}'

        # if the --nohelm arg is present
        if '--nohelm' in args:
            # add /nohelm to the url
            url += '/nohelm'

        # since we want --left and --right to be mutually exclusive,
        # we put them both in a while loop that breaks once one is added
        while True:

            # if the --left arg is present
            if '--left' in args:

                # add /left to the url
                url += '/left'
                break

            # if the --right arg is present
            elif '--right' in args:

                # add /right to the url
                url += '/right'
                break

            else:

                break

        # request the file
        request = BytesIO(requests.get(url).content)

        # change the filename
        request.name = f'{query}.png'

        # Create the file
        file = discord.File(request)

        # send the file
        await ctx.send(file=file)

    # Minecraft Hypixel command
    @_minecraft.command(name='hypixel', aliases=['hp'],
                        help='Get a minecraft user\'s hypixel data')
    async def _minecraft_hypixel(self, ctx, query):

        # create our url for our head display
        avatarurl = f'https://mc-heads.net/combo/{query}'

        # create our request url for the hypixel API
        requrl = f'https://api.hypixel.net/player?key={s.hypixelkey}&name={query}'

        # request the json data
        json = requests.get(requrl).json()

        # if the player key is None that means we could not find the user in the API
        if json['player'] is None:
            # send our error message
            return await ctx.send(f"{self.crossemoji}**I could not find that user in the hypixel API**")

        if "rank" in json["player"] and json["player"]["rank"] != "NORMAL":
            rank = json["player"]["rank"]
        elif "newPackageRank" in json["player"]:
            rank = json["player"]["newPackageRank"]
        elif "packageRank" in json["player"]:
            rank = json["player"]["packageRank"]
        else:
            rank = "Rankless"

        # try and get the last login
        try:

            # get the last time that the user logged in in unix timestamp
            login = json['player']['lastLogin']
            # convert api timestamp to a datetime object
            login = datetime.datetime.fromtimestamp(int(str(login)[:-3]))
            # get the last time that the user logged in in unix timestamp
            flogin = json['player']['firstLogin']
            # convert api timestamp to a datetime object
            flogin = datetime.datetime.fromtimestamp(int(str(flogin)[:-3]))
            # get the last time that the user logged in in unix timestamp
            llogout = json['player']['lastLogout']
            # convert api timestamp to a datetime object
            llogout = datetime.datetime.fromtimestamp(int(str(llogout)[:-3]))

        # if we get an error he login was not found
        except KeyError:
            login = 'Not found'
            # get the last time that the user logged in in unix timestamp
            flogin = json['player']['firstLogin']
            # convert api timestamp to a datetime object
            flogin = datetime.datetime.fromtimestamp(int(str(flogin)[:-3]))
            llogout = 'Not found'

        try:
            swWins = json['player']['stats']['SkyWars']['wins']
        except KeyError:
            swWins = 0

        try:
            hgWins = json['player']['stats']['HungerGames']['wins']
        except KeyError:
            hgWins = 0

        try:
            mmWins = json['player']['stats']['MurderMystery']['wins']
        except KeyError:
            mmWins = 0

        try:
            bwWins = json['player']['stats']['Bedwars']['wins_bedwars']
        except KeyError:
            bwWins = 0

        try:
            duelWins = json['player']['stats']['Duels']['wins']
        except KeyError:
            duelWins = 0

        try:
            pitKills = json['player']['stats']['Pit']['pit_stats_ptl']['kills']
        except KeyError:
            pitKills = 0

        try:
            sbprofiles = len(json['player']['stats']['SkyBlock']['profiles'])
        except KeyError:
            sbprofiles = 0

        try:
            achievements = len(json['player']['achievementsOneTime'])
        except KeyError:
            achievements = 0

        try:
            aliases = json['player']['knownAliasesLower']
        except KeyError:
            aliases = [query]

        # create our embed for the hypixel player
        embed = discord.Embed(title=f'Hypixel Profile for {query}',
                              description='``' + '`` ``'.join(aliases) + '``')

        # add field for login info
        embed.add_field(name='General info',
                        value=f'{self.dashemoji}**First login** '
                              f'``{h.naturaltime(flogin) if flogin != "Not found" else flogin}``\n'
                              f'{self.dashemoji}**Last login:** '
                              f'``{h.naturaltime(login) if login != "Not found" else login}``\n'
                              f'{self.dashemoji}**Last logout** '
                              f'``{h.naturaltime(llogout) if llogout != "Not found" else llogout}``\n'
                              f'{self.dashemoji}**Rank:** ``{rank}``\n'
                              f'{self.dashemoji}**Achievements:** ``{achievements}``')

        # add a field for game stats
        embed.add_field(name='Game stats',
                        value=f'{self.dashemoji}**Skywars Wins:** ``{swWins}``\n'
                              f'{self.dashemoji}**Bedwars Wins:** ``{bwWins}``\n'
                              f'{self.dashemoji}**Murder Mystery Wins:** ``{mmWins}``\n'
                              f'{self.dashemoji}**Hunger Games Wins:** ``{hgWins}``\n'
                              f'{self.dashemoji}**Duel Wins:** ``{duelWins}``\n'
                              f'{self.dashemoji}**Pit Kills:** ``{pitKills}``\n'
                              f'{self.dashemoji}**Skyblock Profiles:** ``{sbprofiles}``')

        # add the user avatar to the embed as the thumbnail
        embed.set_thumbnail(url=avatarurl)

        # send the embed
        await ctx.send(embed=embed)

    # Minecraft Server command
    @_minecraft.command(name='server', aliases=['srv'],
                        help='Get data on any minecraft server.')
    async def _minecraft_server(self, ctx, ip):

        # create our request URL
        requrl = f'https://api.mcsrvstat.us/2/{ip}'

        # request the json data from the API
        json = requests.get(requrl).json()

        # put all the data we need in variables
        # get the server status
        online = json['online']

        # if the server is online
        if not online:
            # send an error message
            return await ctx.send(f"{self.crossemoji}**Server was not found or is not online!**")

        # get server players
        players = f'{json["players"]["online"]}/{json["players"]["max"]}'

        # get server motd
        motd = '\n'.join(json['motd']["clean"])

        # get server version
        version = json["version"]

        # save sever icon to my webserver
        open(f'/media/home/FS2/WEB/blutopia.ca/img/blutonium/{ip}.png', 'wb') \
            .write(base64.decodebytes(bytearray(json['icon'].split(',')[1], encoding='utf-8')))

        # get the url of the server icon
        servericonurl = f'https://proxy.blutopia.ca/img/blutonium/{ip}.png'

        # get server ip
        ipadress = json['ip']

        # try and get the software, some servers wont have this
        try:

            # get server software
            software = json['software']

        # if we get an error
        except KeyError:

            # set software to not found
            software = 'Not found'

        # create our embed for the server
        embed = discord.Embed(title=ip,
                              description=f"**{motd}**",
                              color=0x2F3136)

        # add a field with all the info about our server
        embed.add_field(name="Info", value=f'{self.dashemoji}**Ip:** {ipadress}\n'
                                           f'{self.dashemoji}**Software:** {software}\n'
                                           f'{self.dashemoji}**Version:** {version}\n'
                                           f'{self.dashemoji}**Players:** {players}')

        # set the server icon to the embed thumbnail
        embed.set_thumbnail(url=servericonurl)

        # send the embed
        await ctx.send(embed=embed)

    # serverinfo command is to get and display info about the server
    @commands.command(name='serverinfo', aliases=['guildinfo', 'si', 'sinfo', 'guild'],
                      help='Fetch and display information about the server.')
    async def _serverinfo(self, ctx):

        # get the current guild
        guild: discord.Guild = ctx.guild

        # get the ammount of bots in the server
        botcount = len([user for user in guild.members if user.bot])
        # get the ammount of humans
        humancount = len([user for user in guild.members if not user.bot])
        # get the total members of the server
        usercount = len(guild.members)
        # get the ammount of text channels
        txtChs = len(guild.text_channels)
        # get the ammount of categories
        catCount = len(guild.categories)
        # get the ammount of roles
        roles = len(guild.roles)
        # get the ammount of voice channels
        voicechs = len(guild.voice_channels)

        # get  the guild icon url
        iconurl = guild.icon_url

        # get the guild prefix
        prefix = self.client.fetch_prefix(guild.id)

        # get the guild discovery splasj
        disSplash = (self.checkemoji, guild.discovery_splash_url) \
            if guild.discovery_splash is not None else (self.crossemoji, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ')

        # get the guild banner
        guildbanner = (self.checkemoji, guild.banner_url) \
            if guild.banner is not None else (self.crossemoji, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ')

        # get the guild splash
        guildsplash = (self.checkemoji, guild.splash_url) \
            if guild.splash is not None else (self.crossemoji, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ')

        # get when the guild was created
        created = guild.created_at

        # Get the guild ID
        guildid = guild.id

        # Get the guild region
        region = guild.region

        # get the guildowner
        owner = guild.owner

        # create our embed
        embed = discord.Embed(title=f'{guild}',
                              color=0xFCFCFC,
                              timestamp=datetime.datetime.utcnow(),
                              description=f'***Guild prefix is set to ``{prefix}``***')

        # Add our fields to the embed
        # add the info field
        embed.add_field(name='Guild info', value=f"{self.dashemoji}**ID:** `{guildid}`\n"
                                                 f"{self.dashemoji}**Region:** `{region}`\n"
                                                 f"{self.dashemoji}**Created:** `{h.naturaltime(created)}`\n"
                                                 f"{self.dashemoji}**Owner:** {owner.mention}\n"
                                                 f"{self.dashemoji}**"
                                                 f"[Discovery splash]({disSplash[1]}):** {disSplash[0]}\n"
                                                 f"{self.dashemoji}**"
                                                 f"[Invite splash]({guildsplash[1]}):** {guildsplash[0]}\n"
                                                 f"{self.dashemoji}**"
                                                 f"[Guild banner]({guildbanner[1]}):** {guildbanner[0]}\n")

        # add the stats field
        embed.add_field(name='Guild stats', value=f"{self.dashemoji}**Humans:** `{humancount}`\n"
                                                  f"{self.dashemoji}**Bots:** `{botcount}`\n"
                                                  f"{self.dashemoji}**Total:** `{usercount}`\n"
                                                  f"{self.dashemoji}**Text Channels:** `{txtChs}`\n"
                                                  f"{self.dashemoji}**Voice Channels:** `{voicechs}`\n"
                                                  f"{self.dashemoji}**Categories:** `{catCount}`\n"
                                                  f"{self.dashemoji}**Roles:** `{roles}`")

        # add the guild icon url to the embed
        embed.set_thumbnail(url=iconurl)

        # send the embed
        await ctx.send(embed=embed)

    # Spotify command is to display a user's spotify status
    @commands.command(name='spotify', aliases=['listening'],
                      help='Show a user\'s spotify status', usage='`[userid, name, or mention]`')
    async def _spotify(self, ctx, *, inp=None):

        # fetch the user using the input given
        user = self.client.fetch_member(ctx, inp)

        # for every activity in the user's current activities
        for activity in user.activities:

            # if the activity is an instance of Spotify
            if isinstance(activity, Spotify):
                # get the duration of the song
                dur = chop_microseconds(activity.duration)

                # get the artist of the song
                artist = activity.artist.split(';')[0]

                # get the song title
                song = activity.title.split("(")[0]

                # get the albun that the song is on
                album = activity.album

                # request data about this song on the Genius API
                request = request_song_info(song, artist)

                # try and create a link out of our request
                try:

                    # create the link
                    geniuslink = f'[Lyrics](https://genius.com' \
                                 f'{request.json()["response"]["hits"][0]["result"]["path"]})'

                # if we get an exception that means the request failed
                except Exception:

                    # set the link to just an error message
                    geniuslink = "Failed to find lyrics!"

                # create our embed for the spotify status
                embed = discord.Embed(title=song,
                                      description=f'By **{artist}** on **{album}**',
                                      color=activity.color,
                                      timestamp=activity.created_at)

                # add a field for the duration of the song and the genius lyrics link
                embed.add_field(name="Duration",
                                value=f'{dur}')
                embed.add_field(name="Genius",
                                value=geniuslink)

                # set the footer and thumbnail on the embed
                embed.set_footer(text='Started Listening')
                embed.set_thumbnail(url=activity.album_cover_url)

                # send the embed
                await ctx.send(embed=embed)

    # Avatar command is to show a user's profile picture
    @commands.command(name='avatar', aliases=['av'],
                      help='Fetch a user\'s avatar', usage='`[userid, name, or mention]`')
    async def _avatar(self, ctx, *, inp=None):

        # fetch the user using input
        member = self.client.fetch_member(ctx, inp)

        # get the avatar url
        url = member.avatar_url

        # request the file
        request = BytesIO(requests.get(url).content)

        # change the filename
        # if the avatar is animated
        if member.is_avatar_animated():

            # change the file ext to gif
            request.name = 'avatar.gif'

        # if the avatar is normal
        else:

            # change the file ext to png
            request.name = 'avatar.png'

        # create the file
        file = discord.File(request)

        # send the file
        await ctx.send(file=file)

    # Enlarge command is to show a emoji in a larger fashion
    @commands.command(name='enlarge', aliases=['en', 'big'],
                      help='Enlarge any discord custom emoji')
    async def _enlarge(self, ctx, emoji: discord.PartialEmoji):

        # get the url of the emoji
        url = emoji.url

        # request the file
        request = BytesIO(requests.get(url).content)

        # change the filename
        # if the emoji is animated
        if emoji.animated:

            # change the file extension to gif
            request.name = 'emoji.gif'

        # if its not animated
        else:

            # change the file extension to png
            request.name = 'emoji.png'

        # create the file
        file = discord.File(request)

        # send the file
        await ctx.send(file=file)

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
    @commands.command(name='botinfo', aliases=['stats', 'info', 'binfo', 'about'], help="Get information about the bot.")
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
                      value=f'{serverCount}',
                      inline=True)

        emb.add_field(name='Total Users',
                      value=f'{userCount}',
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
            except IndexError:

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
    @commands.command(name='userinfo', aliases=['ui', 'uinfo', 'profile', 'whois'])
    async def _userinfo(self, ctx, *, user=None):

        # get some emojis from our support server for badges
        balance = get(self.client.emojis, id=780281913172557824)
        briliance = get(self.client.emojis, id=780281707231969341)
        bravery = get(self.client.emojis, id=780281840602447932)
        dnitro = get(self.client.emojis, id=793016993200078848)
        early = get(self.client.emojis, id=793016903441580032)
        staff = get(self.client.emojis, id=793016932903026759)
        botdev = get(self.client.emojis, id=793016951806754856)

        # try and get the user using the input given
        user: discord.Member = self.client.fetch_member(ctx, user)

        # for our first peice of user info were gonna get the permissions that the user has in the guild
        # first we make a list named perms, this will contain all the permissions that we want to display.
        perms = []

        # for every permission that the user has in the guild
        for perm in user.guild_permissions:

            # make a list of permissions that we want to be displayed if the user has them
            key = ['ban members', 'kick members', 'manage messages', 'manage guild',
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
                    perms.append(f'{self.checkemoji}{name.capitalize()}\n')

                # if the name is not in the list of permisssions we want to display
                else:

                    # just continue
                    pass

            # if the user dosent have the permission allowed
            else:

                # get the name of the permission
                name = perm[0]

                # permission names by defauly are formatted like "Manage_Messages" we want to remove the underscore
                # and add a space instead replace the underscore by a space
                name = name.replace('_', ' ')

                # if the name is in the list of permissions that we want to display
                if name in key:

                    # add the name to the list that contains all the permissions we want to display
                    perms.append(f'{self.crossemoji}{name.capitalize()}\n')

                # if the name is not in the list of permisssions we want to display
                else:

                    # just continue
                    pass

        # get our user's join position
        joinpos = find_joinpos(user, ctx.guild)

        # set which emoji we will put on our nitro check field
        nitro = self.checkemoji if checkfornitro(user) else self.crossemoji

        # check if the user is a bot owner
        owner = self.checkemoji if user.id in self.client.owner_ids else self.crossemoji

        # check if the user is blacklisted
        blacklisted = self.checkemoji if user.id in self.client.blacklist_cache else self.crossemoji

        # get all the mutual guilds that the user is in
        mutualguilds = len([1 for guild in self.client.guilds if user in guild.members])

        # initalize our badges string
        badges = ''

        # if any of the user bot dev flags are true
        if user.public_flags.verified_bot_developer \
                or user.public_flags.early_verified_bot_developer \
                or user.public_flags.verified_bot:
            # add the botdev icon
            badges += f'{botdev} '

        # if the staff flag is true
        if user.public_flags.staff:
            # add the staff icon
            badges += f'{staff}'

        # if the user has nitro
        if checkfornitro(user):
            # add the nitro badge
            badges += f'{dnitro} '

        # if the early supporter flag is present
        if user.public_flags.early_supporter:
            # add the early supporer badge
            badges += f'{early} '

        # if the hypesquad balance flag is true
        if user.public_flags.hypesquad_balance:

            # add the balance badge
            badges += f'{balance} '

        # if the briliance flag is true
        elif user.public_flags.hypesquad_brilliance:

            # add the brilliance badge
            badges += f'{briliance} '

        # if the bravery flag is true
        elif user.public_flags.hypesquad_bravery:

            # add the bravery badge
            badges += f'{bravery} '

        # check if the user is a bot VIP
        vip = self.checkemoji if user.id in [393165866285662208, 316689746028003331] else self.crossemoji

        # create our userinfo embed
        embed = discord.Embed(title=f'{user}',
                              color=user.color,
                              timestamp=datetime.datetime.utcnow(),
                              description=f"")

        # add a field for guild specific info
        embed.add_field(name='Guild info', value=f"{self.dashemoji}**Nickname:** {user.display_name}\n"
                                                 f"{self.dashemoji}**Joined at:** {h.naturaltime(user.joined_at)}\n"
                                                 f"{self.dashemoji}**Roles:** {len(user.roles)}\n"
                                                 f"{self.dashemoji}**Join pos:** {joinpos[0]}/{joinpos[1]}")

        # add a field for global info
        embed.add_field(name='Global info', value=f"{self.dashemoji}**ID:** {user.id}\n"
                                                  f"{self.dashemoji}**Created at:** {h.naturaltime(user.created_at)}\n"
                                                  f"{self.dashemoji}**Nitro:** {nitro}\n"
                                                  f"{self.dashemoji}**Badges:** {badges}")

        # add an empty field for design purposes
        embed.add_field(name='\u200b', value='\u200b')

        # add a field for permissions
        embed.add_field(name="Key permissions",
                        value='**' + ''.join(perms) + '**')

        # add a field for bot stats
        embed.add_field(name="Bot Stats", value=f"{self.dashemoji}**Bot owner: {owner}**\n"
                                                f"{self.dashemoji}**Blacklisted:** {blacklisted}\n"
                                                f"{self.dashemoji}**VIP: {vip}**\n"
                                                f"{self.dashemoji}**Shared Guilds:** {mutualguilds}")

        # add an empty field for design purposes
        embed.add_field(name='\u200b', value='\u200b')

        # set the thumbnail of the emebd to the user's avatar
        embed.set_thumbnail(url=user.avatar_url)

        # send the embed
        await ctx.send(embed=embed)

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
