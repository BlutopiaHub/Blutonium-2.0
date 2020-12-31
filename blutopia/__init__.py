# import the neccessary modules
from collections import defaultdict

import datetime
import discord
import os
import pg8000
import platform
import random
from blutopia import setup
from discord.ext import commands
from discord.ext.commands.errors import ExtensionAlreadyLoaded, ExtensionFailed, ExtensionNotFound, \
    ExtensionNotLoaded, NoEntryPointError
from discord.utils import get

__version__ = '1.0.0'


# Define our subclassed client.
class Client(commands.Bot):

    # init code for our subclassed discord bot.
    def __init__(self, **options):

        # Set our variable for our start time. This varaiable is for our uptime command.
        self.start_time = datetime.datetime.now()

        # Set our client Intents.
        clientIntents = discord.Intents.default()
        clientIntents.members = True
        clientIntents.presences = True

        # Init our subclass commands.Bot with our custom prefix method.
        super().__init__(self.findprefix, options=options, intents=clientIntents)

        # Define all our caches.
        self.user_cache = {}
        self.guild_cache = {}
        self.blacklist_cache = []
        self.owner_cache = []
        self.ext_cache = {}
        self.levels_cache = defaultdict(dict)
        self.mute_cache = defaultdict(dict)
        self.hackban_cache = {}

        # Connect to our Database.
        self.db = pg8000.connect(setup.PgName,
                                 host=setup.PgHost,
                                 database=setup.PgDb,
                                 password=setup.PgPwrd,
                                 application_name='Blutonium Client')

        # Set our owner cache to the owner_ids variable. We need to do this so that when we use the @is_owner
        # decorator the owners are known.
        self.owner_ids = self.owner_cache

        # define some custom variables that will be useful for some commands
        self.version = setup.clientVer
        self.pyversion = platform.python_version()
        self.dpyversion = discord.__version__

        # Build all of our client database caches
        self.build_caches()

    # Override our on_message event. This is made so that we can add blacklisting to the method and also add our
    # response to @mentions.
    async def on_message(self, message: discord.Message):

        # get the guild prefix
        try:

            prefix = self.fetch_prefix(message.guild.id)

        # if we get an error it means we got a DM
        except Exception:

            # print our DM
            print(message.content)
            prefix = 'b/'

        # set the message content as its own variable
        msgc = message.content

        # if the message starts with the characters in a mention...
        if msgc.startswith('<@'):

            # if the client user is in the message mentions
            if self.user in message.mentions:
                # define all the frendly responses
                responses = [
                    f'Hey! my prefix for this server is `{prefix}` ',
                    f'No `{prefix}`',
                    f'WHAT DO YOU WA- .. uhh i mean hi. my prefix is `{prefix}`',
                    f'Oi mate heres ya prefix, cheers! `{prefix}`',
                    f'We\'re sorry, {self.user} is unavalible right now. Please use this prefix `{prefix}`',
                    f'imagine forgeting your prefix, `{prefix}`',
                    f'TIP: use `{prefix}cfg prefix (whatever u want)` to change your prefix'
                ]

                # choose a random response
                response = random.choice(responses)

                # send the response
                await message.channel.send(response)

        # if the message author is not in the blacklist
        if message.author.id not in self.blacklist_cache:

            # continue doing bot things
            return await self.process_commands(message)

        # if the user is in the blacklist ...
        else:

            # get the context of the message
            ctx = await self.get_context(message)

            # if the context is valid that means the user tried to invoke a command
            if ctx.valid:
                # send the message saying this user was blacklisted
                return await message.channel.send('You have been blacklisted from using this bot.')

    # Override our load_extension method. This is done so that we can add evey extension that is loaded to the
    # ext_cache along with its start time, for the uptime command.
    def load_extension(self, name: str):

        # try and load the extension normally
        try:
            super().load_extension(name)

        # if we get a ExtensionAlreadyLoaded exception
        except ExtensionAlreadyLoaded:

            # raise the exception
            raise ExtensionAlreadyLoaded(name)

        # if we get an ExtensionNotFound exception
        except ExtensionNotFound:

            # raise the exception
            raise ExtensionNotFound(name)

        # if we get an ExtensionFailed exception
        except ExtensionFailed and Exception as err:

            # raise the exception
            raise ExtensionFailed(name, err)

        # if we get a NoEntryPointError
        except NoEntryPointError:

            # raise the exception
            raise NoEntryPointError(name)

        # if we dont get an error
        else:

            # add the extension to the extension uptime cache
            self.ext_cache[name] = {"start_time": datetime.datetime.now()}

    # Override our unload_extension method. This is done so that we can remove extensions from our ext_cache when
    # extensions our unloaded.
    def unload_extension(self, name: str):

        # try and unload the extension normally
        try:

            # use super() and run the original commands.Bot.unload_extension() method
            super().unload_extension(name)

        # if we get a ExtensionNotLoaded exception
        except ExtensionNotLoaded:

            # raise the exception
            raise ExtensionNotLoaded(name)

        # if everything works
        else:

            # remove the extension from the cache
            self.ext_cache[name] = {}

    # Create our findprefix method. This method is called as the command_prefix. So that we can have different
    # prefixes per server.
    def findprefix(self, client: commands.Bot, message: discord.Message):

        guild = message.guild

        if guild is None:
            return 'b/'

        prefix = self.fetch_prefix(guild.id)

        return prefix

    # set_muterole method is to set the guild muterole
    def set_muterole(self, guildid, roleid):

        self.guild_cache[guildid]['muteroleid'] = roleid

        sql = f"UPDATE guilddata SET muterole = {roleid} WHERE guildid = {guildid}"

        self.db.run(sql)

        self.db.commit()

    # Build_guild_cache method is to add our already saved data from the database to our cache so that we dont have
    # to query our database all the time.
    def build_guild_cache(self):

        sql = f"SELECT guildid, logs, muterole, prefix, logchannelid, warnconfig from guilddata"

        rows = self.db.run(sql)

        for row in rows:
            guildid = row[0]
            logsenabled = row[1]
            muteroleid = row[2]
            prefix = row[3]
            logchannelid = row[4]
            warnconfig = row[5]
            adminroles = self.get_adminroles(guildid)

            self.guild_cache[guildid] = {'logsenabled': logsenabled, 'muteroleid': muteroleid, 'prefix': prefix,
                                         'logchannelid': logchannelid, 'adminroles': adminroles,
                                         'warnconfig': warnconfig}

        return self.guild_cache

    # Build_user_cache method is to add our already saved data from the database to our cache so that we dont have to
    # query our database all the time.
    def build_user_cache(self):

        sql = f"SELECT userid, points, messages, cmduses, claimed, rankimage, ranktext, rankaccent from userdata"

        rows = self.db.run(sql)

        for row in rows:
            userid = row[0]
            points = row[1]
            messages = row[2]
            cmduses = row[3]

            if row[4] is None:

                claimed = row[4]

            elif isinstance(row[4], str):

                claimed = datetime.datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f')

            rankimage = row[5]
            ranktext = row[6]
            rankaccent = row[7]

            self.user_cache[userid] = {"points": points, "messages": messages, "cmduses": cmduses, "claimed": claimed,
                                       "rankimage": rankimage, "ranktext": ranktext, "rankaccent": rankaccent}

        return self.user_cache

    # Build_blacklist_cache method is to add our already saved data from the database to our cache so that we dont
    # have to query our database all the time.
    def build_blacklist_cache(self):

        self.blacklist_cache = []

        sql = f"SELECT * FROM blacklist"

        rows = self.db.run(sql)

        for row in rows:
            userid = row[0]

            self.blacklist_cache.append(userid)

        return self.blacklist_cache

    # Build_owner_cache method is to add our already saved data from the database to our cache so that we dont have
    # to query our database all the time.
    def build_owner_cache(self):

        self.owner_cache = []

        sql = f"SELECT * FROM owners"

        rows = self.db.run(sql)

        for row in rows:
            uid = row[0]

            self.owner_cache.append(uid)

        self.owner_ids = self.owner_cache
        return self.owner_cache

    # Build_level_cache method is to add our already saved data from the database to our cache so that we dont have
    # to query our database all the time.
    def build_level_cache(self):

        sql = f"SELECT * from levels"

        rows = self.db.run(sql)

        for row in rows:
            guildid = row[0]
            userid = row[1]
            currentlevel = row[2]
            currentxp = row[3]
            requiredxp = row[4]

            if row[5] is None:

                lastxp = row[5]

            elif isinstance(row[5], str):

                lastxp = datetime.datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S.%f')

            self.levels_cache[guildid][userid] = {"currentlevel": currentlevel, "currentxp": currentxp,
                                                  "requiredxp": requiredxp, "lastxp": lastxp}

        return self.levels_cache

    # Build_mute_cache method is to add our already saved data from the database to our cache so that we dont have to
    # query out database all the time.
    def build_mute_cache(self):

        sql = f"SELECT * FROM mutes"

        rows = self.db.run(sql)

        for row in rows:
            guildid = row[0]
            muteid = row[1]
            reason = row[2]
            time = datetime.datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f')
            modid = row[4]

            self.mute_cache[guildid][muteid] = {"active": True, 'reason': reason, 'time': time, 'modid': modid}

        return self.mute_cache

    # Build_hackban cache is another cache building method.
    def build_hackban_cache(self):

        for guild in self.guilds:
            self.hackban_cache[guild.id] = {'users': []}

        sql = "SELECT * FROM hackbans"

        rows = self.db.run(sql)

        for row in rows:

            guildid = row[0]
            userid = row[1]

            try:
                self.hackban_cache[guildid]['users'].append(userid)
            except Exception:
                pass

    # Build_caches method is to build our various caches that we have in one method.
    def build_caches(self):

        # Build all our caches.
        self.build_guild_cache()
        self.build_user_cache()
        self.build_blacklist_cache()
        self.build_owner_cache()
        self.build_level_cache()
        self.build_mute_cache()
        self.build_hackban_cache()

    # Fetch_prefix method is to fetch a prefix for a guild from our cache.
    def fetch_prefix(self, guildid: int):

        if guildid in self.guild_cache.keys():

            return self.guild_cache[guildid]['prefix']

        else:

            return 'b/'

            # Update prefix method is to update prefixes in our cache and database.

    def update_prefix(self, guildid: int, prefix: str):

        sql = f"UPDATE guilddata SET prefix = '{prefix}' WHERE guildid = {guildid}"

        self.guild_cache[guildid]['prefix'] = prefix

        self.db.run(sql)
        self.db.commit()

    # blacklist method is to update the blackist and add a user to it.
    def blacklist(self, userid: int):

        sql = f"INSERT INTO blacklist (userid) VALUES ({userid})"
        self.db.run(sql)

        self.blacklist_cache.append(userid)

        self.db.commit()

    # unblacklist method is to update the blacklist and remove a user to it.
    def unblacklist(self, userid: int):

        sql = f"DELETE FROM blacklist WHERE userid = {userid}"
        self.db.run(sql)

        self.blacklist_cache.remove(userid)

        self.db.commit()

    # All_users_data_build is to add every user that isnt in the databse into the database.
    def all_users_data_build(self):

        # for every user that the client can see
        for user in self.get_all_members():
            sql = f"INSERT INTO userdata (userid, points, messages, cmduses, claimed, rankimage, ranktext, " \
                  f"rankaccent) VALUES ({user.id},0,0,0,null,null,null,null) ON CONFLICT DO NOTHING "

            self.db.run(sql)

        self.build_user_cache()

        self.db.commit()
        return

    # all guilds level data build generates all the missing level data in all the guilds
    def all_guilds_level_data_build(self):

        # for every guild that the clientuser is in
        for guild in self.guilds:

            # generate the guild level data
            self.generate_mass_level_data(guild)

        # build the level cache to add all our newest users
        self.build_level_cache()

    # generate mass level data is to generate all the level data in a guild
    def generate_mass_level_data(self, guild):

        # for every member of the guild
        for member in guild.members:

            # create our sql statement
            sql = f"INSERT INTO levels (guildid, userid, currentlevel, currentxp, requiredxp, lastxp)" \
                  f"VALUES ({guild.id}, {member.id}, 0, 0, default, null) ON CONFLICT DO NOTHING"

            # run the sql
            self.db.run(sql)

        # commit the db
        self.db.commit()

    # generate level data is to generate level data for a single user
    def generate_level_data(self, userid, guildid):

        # create our sql statement
        sql = f"INSERT INTO levels (guildid, userid, currentlevel, currentxp, requiredxp, lastxp)" \
              f"VALUES ({guildid}, {userid}, 0, 0, default, null) ON CONFLICT DO NOTHING"

        # run the sql
        self.db.run(sql)

        # commit the db
        self.db.commit()

        # add the new user to the cache
        self.levels_cache[guildid][userid] = {"currentlevel": 0, "currentxp": 0,
                                              "requiredxp": 100, "lastxp": None}

    # level user our method that will be run on every message to do the level shit
    def leveluser(self, userid, guildid):

        # get the level data right now
        leveldata = self.levels_cache[guildid][userid]

        # turn all thedata into variables
        lastxp = leveldata['lastxp']
        currentxp = leveldata['currentxp']
        currentlevel = leveldata['currentlevel']
        requiredxp = leveldata['requiredxp']

        # if the lastxp key is a datetime
        if isinstance(leveldata['lastxp'], datetime.datetime):

            cooldown = lastxp + datetime.timedelta(seconds=60)

        # if it isnt that means its a Nonetype
        else:

            cooldown = datetime.datetime.now() - datetime.timedelta(seconds=1)

        # intitialize our leveldup variable which will be returned at the end
        # of this method
        leveldup = (0, 0)
        
        # get the time now
        now = datetime.datetime.now()

        # change now to a string for the database
        strnow = now.strftime('%Y-%m-%d %H:%M:%S.%f')

        # if the cooldown is over
        if now >= cooldown:

            # create the random ammount of xp that the user recieves
            xp_gained = random.randrange(5, 10)

            # calculate the new ammount of xp that the user has
            newxp = currentxp + xp_gained

            # if the new xp is over the user's required xp
            if newxp >= requiredxp:

                # reset our user's xp and add the excess xp
                vnewxp = xp_gained + (requiredxp - currentxp)

                # increment the level
                newlevel = currentlevel + 1

                # change our leveldup variable that is returned
                leveldup = (1, newlevel)

                # update the database
                self.db.run(f"UPDATE levels SET (currentxp, lastxp, currentlevel) = "
                            f"({vnewxp}, '{strnow}', {newlevel}) WHERE userid = {userid} AND guildid = {guildid}")

                # update the cache
                self.levels_cache[guildid][userid]['currentlevel'] = newlevel
                self.levels_cache[guildid][userid]['currentxp'] = vnewxp
                self.levels_cache[guildid][userid]['lastxp'] = now

            # if the xp is not over the user's required xp
            else:

                # update the db
                self.db.run(f"UPDATE levels SET (currentxp, lastxp) = "
                            f"({newxp}, '{strnow}') WHERE userid = {userid} AND guildid = {guildid}")

                # update the cache
                self.levels_cache[guildid][userid]['currentxp'] = newxp
                self.levels_cache[guildid][userid]['lastxp'] = now

        # commit the database changes
        self.db.commit()

        # return our leveldup var
        return leveldup

    def fetch_level_data(self, guildid, userid):

        return self.levels_cache[guildid][userid]

    def fetch_user_data(self, userid):
        return self.user_cache[userid]

    def set_ranktext(self, userid, text):

        sql = f"UPDATE userdata SET ranktext = '{text}' WHERE userid = {userid}"

        self.db.run(sql)
        self.user_cache[userid]['ranktext'] = text

        self.db.commit()

    def set_accent(self, userid, accent):

        sql = f"UPDATE userdata SET rankaccent = '{accent}' WHERE userid = {userid}"

        self.db.run(sql)
        self.user_cache[userid]['rankaccent'] = accent

        self.db.commit()

    def set_rankbg(self, userid, link):

        sql = f"UPDATE userdata SET rankimage = '{link}' WHERE userid = {userid}"

        self.db.run(sql)
        self.user_cache[userid]['rankimage'] = link

        self.db.commit()

    # All_guilds_data_build is to add every user that isnt in the database into the database.
    async def all_guilds_data_build(self):

        class fakeRole:

            def __init__(self):
                self.id = 000000000000000000000

        for guild in self.guilds:

            sql = f"SELECT guildid FROM guilddata WHERE guildid = {guild.id}"

            rows = self.db.run(sql)

            if rows:
                continue

            logs = True

            logchan = get(guild.channels, name='logs')

            if logchan is None:
                logchan = get(guild.channels, name='Logs')

            if logchan is None:
                logchan = 0
                logs = False

            try:

                muterole = await self.fetch_mute_role(guild)

            except Exception:

                muterole = fakeRole()

            prefix = 'b/'

            sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES " \
                  f"({guild.id},null,{logs},{muterole.id},'{prefix}',{logchan}) ON CONFLICT DO NOTHING "

            try:

                self.db.run(sql)

            except Exception:

                sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES " \
                      f"({guild.id}, null, {logs}, {muterole.id}, 'b/', 0 ) ON CONFLICT DO NOTHING"

                self.db.run(sql)

            path = f"/media/home/FS2/WEB/blutopia.ca/img/blutonium/{guild.id}"
            if not os.path.exists(path):
                os.mkdir(path)

            continue

        self.build_guild_cache()
        self.db.commit()
        return

    # Fetch_mute_role is to get the mute role from any guild.
    async def fetch_mute_role(self, guild: discord.Guild):

        class fakeRole:

            def __init__(self):
                self.id = 000000000000000000000

        try:

            role = self.guild_cache[guild.id]['muteroleid']

        except Exception:

            role = None

        if not role:

            muterole = get(guild.roles, name='Muted')

            if muterole is None:
                muterole = get(guild.roles, name='muted')

            if muterole is None:

                try:

                    role = await guild.create_role(name='muted')

                except Exception:

                    print(f"Unable to create muted role for {guild}")
                    muterole = fakeRole()

                    sql = f"UPDATE guilddata SET muterole  = {muterole.id} WHERE guildid = {guild.id}"
                    self.db.run(sql)
                    self.guild_cache[guild.id]['muteroleid'] = muterole.id

                    self.db.commit()

                    return muterole

                for channel in guild.text_channels:
                    await channel.set_permissions(role, send_messages=False, read_messages=True)

                sql = f"UPDATE guilddata SET muterole = {role.id} WHERE guildid = {guild.id}"
                self.db.run(sql)
                self.guild_cache[guild.id]['muteroleid'] = role.id

                self.db.commit()
                return role

            sql = f"UPDATE guilddata SET muterole = {muterole.id} WHERE guildid = {guild.id}"
            self.db.run(sql)
            self.guild_cache[guild.id]['muteroleid'] = muterole.id

            self.db.commit()
            return muterole

        try:
            muterole = get(guild.roles, id=role)

        except Exception:

            muterole = None

        return muterole

        # Create_user is to add individual users to our databse.

    def create_user(self, user: discord.Member):

        sql = f"INSERT INTO userdata (userid, points, messages, cmduses, claimed, rankimage, ranktext, rankaccent) " \
              f"VALUES ({user.id},0,0,0,null,null,null,null) ON CONFLICT DO NOTHING"
        self.user_cache[user.id] = {"points": 0, "messages": 0, "cmduses": 0, "claimed": None, "rankimage": None,
                                    "ranktext": None, "rankaccent": None}
        self.db.run(sql)

        self.db.commit()
        return

        # Log_guild is to add individual guilds to our database.

    async def log_guild(self, guild: discord.Guild):

        class fakeRole:

            def __init__(self):
                self.id = 000000000000000000000

        sql = f"SELECT guildid FROM guilddata WHERE guildid = {guild.id}"

        rows = self.db.run(sql)

        if rows:
            return

        logs = True

        logchan = get(guild.channels, name='logs')

        if logchan is None:
            logchan = get(guild.channels, name='Logs')

        if logchan is None:
            logchan = 0
            logs = False

        try:

            muterole = await self.fetch_mute_role(guild)

        except Exception:

            muterole = fakeRole()

        prefix = 'b/'

        sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES " \
              f"({guild.id},null,{logs},{muterole.id},'{prefix}',{logchan}) ON CONFLICT DO NOTHING"

        try:

            self.db.run(sql)

        except Exception:

            sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES " \
                  f"({guild.id}, null, {logs}, {muterole.id}, 'b/', 0 ) ON CONFLICT DO NOTHING"

            self.db.run(sql)

        path = f"/media/home/FS2/WEB/blutopia.ca/img/blutonium/{guild.id}"
        if not os.path.exists(path):
            os.mkdir(path)

        self.db.commit()
        return

    # Set_owner is to add a user to the owners list.
    def set_owner(self, userid: int):

        sql = f"INSERT INTO owners (userid) VALUES ({userid}) ON CONFLICT DO NOTHING"

        self.db.run(sql)

        self.owner_cache.append(userid)

        self.db.commit()

    # Remove_owner is to delete a user from the owners list.
    def remove_owner(self, userid: int):

        sql = f"DELETE FROM owners WHERE userid={userid}"

        self.db.run(sql)

        self.owner_cache.remove(userid)

        self.db.commit()

    # Fetch_member is to get a member using the user command input.
    @staticmethod
    def fetch_member(ctx: commands.Context, inp: str):

        member = None

        try:
            member = get(ctx.guild.members, id=int(inp))

        except Exception:

            if inp:

                member = get(ctx.guild.members, name=inp)

                if member is None:
                    member = get(ctx.guild.members, display_name=inp)

                try:
                    if member is None:
                        bro = inp.split('#')

                        member = get(ctx.guild.members, name=bro[0], discriminator=bro[1])

                except IndexError:

                    if inp is None:
                        member: discord.Member = ctx.author
                    else:
                        for men in ctx.message.mentions:
                            member = men

            if inp is None:
                member: discord.Member = ctx.author
            else:
                for men in ctx.message.mentions:
                    member = men

        return member

    # Fetch_log_data is to fetch the logging settings from the cache.
    def fetch_log_data(self, guild: discord.Guild):

        data = (guild.id, self.guild_cache[guild.id]["logsenabled"], self.guild_cache[guild.id]["logchannelid"])

        if data[2] == 0:

            chan = get(guild.channels, name='logs')

            if chan is None:
                chan = get(guild.channels, name='Logs')

            if chan is None:

                # make loggingfalse
                self.guild_cache[guild.id]["logsenabled"] = False
                data = (guild.id, False, 0)

            else:

                # make the channel this new found channel
                self.guild_cache[guild.id]["logchannelid"] = chan.id

        return data

        # Update_Log_channel is to change the channel that blutonium will log in a given guild

    def update_log_channel(self, guild: discord.Guild, channelid: int):

        self.fetch_log_data(guild)

        sql = f"UPDATE guilddata SET logchannelid = {channelid} WHERE guildid = {guild.id}"

        self.db.run(sql)
        self.guild_cache[guild.id]['logchannelid'] = channelid

        self.db.commit()

        return 0

    # Toggle_logs is to toggle logging in a given guild
    def set_logs(self, guildid: int, state: bool):

        self.guild_cache[guildid]['logsenabled'] = state

        state = 'true' if state else 'false'

        sql = f'UPDATE guilddata SET logs = {state} WHERE guildid = {guildid}'

        self.db.run(sql)

        self.db.commit()

    # Fetch_simple_member fetches a member using the user input from the command but ths one only get's @mentions and
    # user IDs no names or nicknames
    @staticmethod
    def fetch_simple_member(ctx: commands.Context, inp: str):

        # set the user variable to None this means the method will return None if the fetch doesnt work
        user = None

        # try and get the user using the unput
        try:

            # we turn the input to an INT
            inp = int(inp)

            user = get(ctx.guild.members, id=inp)

        # when we get a Errror that means the user didnt input a ID
        except ValueError:

            # try and get the message mentions
            if ctx.message.mentions:
                # get the first mention
                user = ctx.message.mentions[0]

        # return the user
        return user

        # Mute Is to add a mute to our cache and database

    def mute(self, guildid: int, userid: int, modid: int, reason: str, time: datetime.date):

        sql = f"INSERT INTO mutes (guildid, mutedid, reason, time, modid) VALUES " \
              f"({guildid}, {userid}, '{reason}', '{time.strftime('%Y-%m-%d %H:%M:%S.%f')}', {modid})" \
              f" ON CONFLICT DO NOTHING"

        self.db.run(sql)
        self.mute_cache[guildid][userid] = {'active': True, 'modid': modid, 'reason': reason, 'time': time}

        self.db.commit()

    # Fetch Mutes is to get all he mutes in a given guild
    def fetch_mutes(self, guildid: int):

        sql = f"SELECT * FROM mutes WHERE guildid = {guildid}"

        rows = self.db.run(sql)

        return rows

    # fetch_active_mutes is essentially the same as fetch_mutes but this method querys our cache instead of our
    # database so that our unmute loop can run faster.
    def fetch_active_mutes(self, guildid: int):

        mutes = []

        for x in self.mute_cache[guildid]:

            if self.mute_cache[guildid][x]['active']:
                time = self.mute_cache[guildid][x]['time']
                reason = self.mute_cache[guildid][x]['reason']
                modid = self.mute_cache[guildid][x]['modid']

                mute = (guildid, x, reason, time, modid)

                mutes.append(mute)

        return mutes

    # Unmute is to remove a mute from our cache and database
    def unmute(self, guildid, userid):

        sql = f"DELETE FROM mutes WHERE mutedid = {userid} AND guildid = {guildid}"

        self.db.run(sql)
        self.mute_cache[guildid][userid]['active'] = False

        self.db.commit()

    # Hackban is to add a user to the hackban cache and database
    def hackban(self, guildid: int, userid: int, reason: str):

        sql = f"INSERT INTO hackbans (guildid, userid, reason) VALUES ({guildid}, {userid}, '{reason}')" \
              f" ON CONFLICT DO NOTHING"

        self.db.run(sql)
        self.hackban_cache[guildid]['users'].append(userid)

        self.db.commit()

    # Unhackban is to delete a user from the hackban cache and datbase
    def unhackban(self, guildid: int, userid: int):

        sql = f"DELETE FROM hackbans WHERE userid={userid} AND guildid={guildid}"

        self.db.run(sql)
        self.hackban_cache[guildid]['users'].remove(userid)

        self.db.commit()

    # Fetch_hackbans is to get all the hackbans from a specific guild.
    def fetch_hackbans(self, guildid: int):

        sql = f"SELECT * FROM hackbans WHERE guildid={guildid}"

        rows = self.db.run(sql)

        self.db.commit()

        return rows

    # Warn command is to add a warn to a user in a specific guild
    def warn(self, guildid: int, userid: int, caseid: int, modid: int, reason: str):

        sql = f"INSERT INTO warns (guildid, userid, caseid, modid, reason) VALUES " \
              f"({guildid}, {userid}, {caseid}, {modid}, '{reason}') ON CONFLICT DO NOTHING"

        self.db.run(sql)

        self.db.commit()

    # Unwarn command is to remove a specific warn from a user
    def unwarn(self, guildid: int, caseid: int):

        sql = f"DELETE FROM warns WHERE caseid = {caseid} AND guildid = {guildid}"

        self.db.run(sql)

        self.db.commit()

    # Fetch_warns is to fetch all a users warns in a specific guild
    def fetch_warns(self, guildid: int, userid: int):

        sql = f"SELECT * FROM warns WHERE userid={userid} AND guildid={guildid}"

        rows = self.db.run(sql)

        return rows

    # Fetch_warns_given is to fetch all the warns that a user has issued in a given server
    def fetch_warns_given(self, guildid: int, modid: int):

        sql = f"SELECT * FROM warns WHERE modid = {modid} AND guildid = {guildid}"

        rows = self.db.run(sql)

        return rows

    # fetch_all_warns gets all the warns for the specific guild
    def fetch_all_warns(self, guildid: int):

        sql = f"SELECT * FROM warns WHERE guildid={guildid}"

        rows = self.db.run(sql)

        return rows

    def fetch_adminroles(self, guildid: int):

        return self.guild_cache[guildid]['adminroles']

    def get_adminroles(self, guildid: int):

        sql = f"SELECT adminroles FROM guilddata WHERE guildid={guildid}"

        rows = self.db.run(sql)

        return rows[0][0]

    def add_adminrole(self, guildid: int, roleid: int):

        adminroles = self.fetch_adminroles(guildid)

        if adminroles is None:
            adminroles = []

        adminroles.append(roleid)

        adminroles_string = '{' + ','.join((str(x) for x in adminroles)) + '}'

        sql = f'UPDATE guilddata SET adminroles = \'{adminroles_string}\' WHERE guildid = {guildid}'

        self.db.run(sql)
        self.guild_cache[guildid]['adminroles'] = adminroles
        self.db.commit()

    def remove_adminrole(self, guildid: int, roleid: int):

        adminroles = self.fetch_adminroles(guildid)

        adminroles.remove(roleid)

        adminroles_string = '{' + ','.join((str(x) for x in adminroles)) + '}'

        sql = f'UPDATE guilddata SET adminroles = \'{adminroles_string}\' WHERE guildid = {guildid}'

        self.db.run(sql)
        self.guild_cache[guildid]['adminroles'] = adminroles
        self.db.commit()

    def set_autoban(self, guildid: int, state: bool):

        self.guild_cache[guildid]['warnconfig']['autoban'] = state

        state = 'true' if state else 'false'

        maxwarns = self.guild_cache[guildid]['warnconfig']['maxwarns']

        sql = f'UPDATE guilddata SET warnconfig = ' \
              f'\'{{"autoban": {state}, "maxwarns": {maxwarns}}}\' WHERE guildid = {guildid}'

        self.db.run(sql)

        self.db.commit()

    def set_maxwarns(self, guildid: int, ammount: int):

        autoban = self.guild_cache['warnconfig']['autoban']

        autoban = 'true' if autoban else 'false'

        self.guild_cache[guildid]['warnconfig']['maxwarns'] = ammount

        sql = f'UPDATE guilddata SET warnconfig = ' \
              f'\'{{"autoban":{autoban}, "maxwarns":{ammount}}}\' WHERE guildid = {guildid}'

        self.db.run(sql)
        self.db.commit()

    def fetch_points(self, userid: int):

        return self.user_cache[userid]['points']

    def fetch_claimed(self, userid: int):

        # fetch when the last time the points were claimed
        claimed = self.user_cache[userid]['claimed']

        # if our last claimed is None that means the user has never claimed points
        if claimed is None:

            # get the datetime now
            now = datetime.datetime.now()

            # add 24 hours to now to get the next time the user can claim their points
            nextclaim = now + datetime.timedelta(hours=24)

            # turn now into a string for the database
            strnow = now.strftime('%Y-%m-%d %H:%M:%S.%f')

            # set the last claim in the cache to the now
            self.user_cache[userid]['claimed'] = now

            # set the last claim in the db to now
            sql = f'UPDATE userdata SET claimed =  \'{strnow}\' WHERE userid = {userid}'
            self.db.run(sql)
            self.db.commit()

            # we will return a tuple with a boolean and a datetime, the datetime will be when our next claim is avalible
            # and the boolean will be wether we can claim the 100 points right now or if were waiting
            return True, nextclaim

        # if the last claimed is not None
        else:

            # get the datetime now
            now = datetime.datetime.now()

            # get our next claim
            # the next claim is 24 hours from our last claim
            nextclaim = claimed + datetime.timedelta(hours=24)

            # if our next claim is more than now Which means its in the future that means we cant claim yet
            # we will only claim once our next claim has passed
            if now < nextclaim:

                # we will return false and a datetime of when our next claim is
                return False, nextclaim

            # if our next claim has passed
            else:

                # our nextclaim will become our last claimed
                self.user_cache[userid]['claimed'] = now

                # turn nextclaim into a string for the database
                strlast = nextclaim.strftime('%Y-%m-%d %H:%M:%S.%f')

                # update the database
                sql = f'UPDATE userdata SET claimed = \'{strlast}\' WHERE userid = {userid}'
                self.db.run(sql)
                self.db.commit()

                # we will return True and a now datetime, in this case whatever datetime object we return doesnt matter
                # because we arent gonna use it
                return True, now

    def set_points(self, userid: int, ammount: int):

        # update the cache with our new points ammount
        self.user_cache[userid]['points'] = ammount

        # update the database with our new points ammount
        sql = f"UPDATE userdata SET points = {ammount} WHERE userid = {userid}"
        self.db.run(sql)
        self.db.commit()

    def fetch_guild_points_leaderboard(self, guildmembers: list):

        # make an empty list called ids
        ids = []

        # for every user in the guild
        for member in guildmembers:
            # add the user's id to the ids list
            ids.append(member.id)

        # change the ids list to a string and change the square brackets to normal brackets
        ids = str(ids).replace('[', '(') \
            .replace(']', ')')

        # create our database query
        sql = f"SELECT userid, points FROM userdata WHERE userid IN {ids} ORDER BY points DESC LIMIT 10"

        # query the database
        rows = self.db.run(sql)

        # return the query
        return rows

    def fetch_level_data(self, userid: int, guildid: int):

        return self.levels_cache[guildid][userid]

    # override our run command to add some of our own spice
    def run(self, *args, **kwargs):

        print("Client starting...\n")
        super().run(*args, **kwargs)
        print("Thank you for using Blutonium Client")
