# import the neccessary modules
from discord.ext.commands.errors import ExtensionAlreadyLoaded, ExtensionError, ExtensionFailed, ExtensionNotFound, ExtensionNotLoaded, NoEntryPointError
from discord.ext import commands
from discord.utils import get
from collections import defaultdict
import pg8000, setup, datetime, discord, random, platform, os

# Define our subclassed client.
class Client(commands.Bot):

    # init code for our subclassed discord bot.
    def __init__(self, **options):

        # Set our variable for our start time. This varaiable is for our uptime command.
        self.start_time = datetime.datetime.now()

        # Set our client Intents.
        clientIntents           = discord.Intents.default()
        clientIntents.members   = True
        clientIntents.presences = True

        # Init our subclass commands.Bot with our custom prefix method. 
        super().__init__(self.findprefix, options=options, intents=clientIntents)

        # Define all our caches. 
        self.user_cache      = {}
        self.guild_cache     = {}
        self.blacklist_cache = []
        self.owner_cache     = []
        self.ext_cache       = {}
        self.levels_cache    = defaultdict(dict)
        self.mute_cache      = defaultdict(dict)
        self.hackban_cache   = {}

        # Connect to our Database. 
        self.db              = pg8000.connect(setup.PgName, host=setup.PgHost, database=setup.PgDb, password=setup.PgPwrd, application_name='Blutonium Client')

        # Set our owner cache to the owner_ids variable. We need to do this so that when we use the @is_owner decorator the owners are known.
        self.owner_ids       = self.owner_cache

        # define some custom variables that will be useful for some commands
        self.version = setup.clientVer
        self.pyversion = platform.python_version()
        self.dpyversion = discord.__version__

        # Build all of our client database caches
        self.build_caches()

    # Override our on_message event. This is made so that we can add blacklisting to the method and also add our response to @mentions.
    async def on_message(self, message):
        
        
        # get the guild prefix
        try:

            prefix  = self.fetch_prefix(message.guild.id)
        
        # if we get an error it means we got a DM
        except:

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

    # Override our load_extension method. This is done so that we can add evey extension that is loaded to the ext_cache along with its start time, for the uptime command.
    def load_extension(self, name):

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
            raise ExtensionFailed(name,err)
        
        # if we get a NoEntryPointError
        except NoEntryPointError:  

            # raise the exception
            raise NoEntryPointError(name)

        # if we dont get an error
        else:
            
            # add the extension to the extension uptime cache
            self.ext_cache[name] = {"start_time" : datetime.datetime.now()}
    
    # Override our unload_extension method. This is done so that we can remove extensions from our ext_cache when extensions our unloaded.
    def unload_extension(self, name):

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

    # Create our findprefix method. This method is called as the command_prefix. So that we can have different prefixes per server.
    def findprefix(self, client, message):

        guild  = message.guild

        if guild is None:

            return 'b/'

        prefix = self.fetch_prefix(guild.id)

        return prefix

    # Build_guild_cache method is to add our already saved data from the database to our cache so that we dont have to query our database all the time.
    def build_guild_cache(self):

        sql = f"SELECT guildid, logs, muterole, prefix, logchannelid from guilddata"

        rows = self.db.run(sql)

        for row in rows:

            guildid      = row[0]
            logsenabled  = row[1]
            muteroleid   = row[2]
            prefix       = row[3]
            logchannelid = row[4]

            self.guild_cache[guildid] = {'logsenabled' : logsenabled, 'muteroleid' : muteroleid, 'prefix' : prefix, 'logchannelid' : logchannelid}

        return self.guild_cache
    
    # Build_user_cache method is to add our already saved data from the database to our cache so that we dont have to query our database all the time.
    def build_user_cache(self):

        sql  = f"SELECT userid, points, messages, cmduses, claimed, rankimage, ranktext, rankaccent from userdata"

        rows = self.db.run(sql)

        for row in rows:

            userid     = row[0]
            points     = row[1]
            messages   = row[2]
            cmduses    = row[3]
            claimed    = row[4]
            rankimage  = row[5]
            ranktext   = row[6]
            rankaccent = row[7]

            self.user_cache[userid] = {"points" : points, "messages" : messages, "cmduses" : cmduses, "claimed" : claimed, "rankimage" : rankimage, "ranktext" : ranktext, "rankaccent" : rankaccent}      

        return self.user_cache

    # Build_blacklist_cache method is to add our already saved data from the database to our cache so that we dont have to query our database all the time.
    def build_blacklist_cache(self):

        self.blacklist_cache = []

        sql = f"SELECT * FROM blacklist"

        rows = self.db.run(sql)

        for row in rows:

            id = row[0]
            
            self.blacklist_cache.append(id)

        return self.blacklist_cache
    
    # Build_owner_cache method is to add our already saved data from the database to our cache so that we dont have to query our database all the time.
    def build_owner_cache(self):

        self.owner_cache = []

        sql = f"SELECT * FROM owners"

        rows = self.db.run(sql)

        for row in rows:

            id = row[0]

            self.owner_cache.append(id)
        
        self.owner_ids = self.owner_cache
        return self.owner_cache
    
    # Build_level_cache method is to add our already saved data from the database to our cache so that we dont have to query our database all the time.
    def build_level_cache(self):

        sql = f"SELECT * from levels"
        
        rows = self.db.run(sql)

        for row in rows:   

            guildid = row[0]
            userid = row[1]
            currentlevel = row[2]
            currentxp = row[3]
            requiredxp = row[4]
            lastxp = row[5]

            self.levels_cache[guildid][userid] = {"currentlevel":currentlevel, "currentxp":currentxp,"requiredxp":requiredxp, "lastxp":lastxp}

        return self.levels_cache

    # Build_mute_cache method is to add our already saved data from the database to our cache so that we dont have to query out database all the time.
    def build_mute_cache(self):

        sql = f"SELECT * FROM mutes"

        rows = self.db.run(sql)

        for row in rows:

            guildid = row[0]
            muteid = row[1]
            reason = row[2]
            time = datetime.datetime.strptime(row[3],'%Y-%m-%d %H:%M:%S.%f') 
            modid = row[4]

            self.mute_cache[guildid][muteid] = {"active":True,'reason':reason,'time':time,'modid':modid}

        return self.mute_cache

    # Build_hackban cache is another cache building method.
    def build_hackban_cache(self):

        for guild in self.guilds:

            self.hackban_cache[guild.id] = {'users':[]}

        sql = "SELECT * FROM hackbans"

        rows = self.db.run(sql)

        for row in rows:

            guildid = row[0]
            userid = row[1]
            reason = row[2]

            try:
                self.hackban_cache[guildid]['users'].append(userid)
            except:
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
    def fetch_prefix(self, guildid):

        if guildid in self.guild_cache.keys():

            return self.guild_cache[guildid]['prefix']

        else:

            return 'b/'     

    # Update prefix method is to update prefixes in our cache and database.
    def update_prefix(self, guildid, prefix):

        sql = f"UPDATE guilddata SET prefix = '{prefix}' WHERE guildid = {guildid}"

        self.guild_cache[guildid]['prefix'] = prefix

        self.db.run(sql)
        self.db.commit()

    # blacklist method is to update the blackist and add a user to it.
    def blacklist(self, id):

        sql = f"INSERT INTO blacklist (userid) VALUES ({id})"
        self.db.run(sql)

        self.blacklist_cache.append(id)

        self.db.commit()

    # unblacklist method is to update the blacklist and remove a user to it.
    def unblacklist(self, id):

        sql = f"DELETE FROM blacklist WHERE userid = {id}"
        self.db.run(sql)

        self.blacklist_cache.remove(id)

        self.db.commit()
    
    # All_users_data_build is to add every user that isnt in the databse into the database.
    def all_users_data_build(self):

        # for every user that the client can see
        for user in self.get_all_members():

            sql = f"INSERT INTO userdata (userid, points, messages, cmduses, claimed, rankimage, ranktext, rankaccent) VALUES ({user.id},0,0,0,null,null,null,null) ON CONFLICT DO NOTHING"
            self.user_cache[user.id] = {"points" : 0, "messages" : 0, "cmduses" : 0, "claimed" : None, "rankimage" : None, "ranktext" : None, "rankaccent" : None}
            self.db.run(sql)

        self.db.commit()
        return

    # All_guilds_data_build is to add every user that isnt in the database into the database.
    async def all_guilds_data_build(self):

        class fakeRole():

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
                logs =  False
            
            try:

                muterole = await self.fetch_mute_role(guild)
            
            except:

                muterole = fakeRole()
            
            prefix = 'b/'

            sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES ({guild.id},null,{logs},{muterole.id},'{prefix}',{logchan}) ON CONFLICT DO NOTHING"

            try:
                
                rows = self.db.run(sql)
            
            except:

                sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES ({guild.id}, null, {logs}, {muterole.id}, 'b/', 0 ) ON CONFLICT DO NOTHING"

                rows = self.db.run(sql)
        
            path = f"/media/home/FS2/WEB/blutopia.ca/img/blutonium/{guild.id}"
            if not os.path.exists(path):

                os.mkdir(path)

            continue

        self.db.commit()
        return
    
    # Fetch_mute_role is to get the mute role from any guild.
    async def fetch_mute_role(self, guild):

        class fakeRole():

            def __init__(self):

                self.id = 000000000000000000000

        try:

            role = self.guild_cache[guild.id]['muteroleid']
        
        except:

            role = None

        if not role:

            muterole = get(guild.roles, name='Muted')

            if muterole is None:
                
                muterole = get(guild.roles, name='muted')

            if muterole is None:

                try:

                    role = await guild.create_role(name='muted')
                
                except:

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

        except:

            muterole = None

        return muterole   
    
    # Create_user is to add individual users to our databse.
    def create_user(self, user):

        sql = f"INSERT INTO userdata (userid, points, messages, cmduses, claimed, rankimage, ranktext, rankaccent) VALUES ({user.id},0,0,0,null,null,null,null) ON CONFLICT DO NOTHING"
        self.user_cache[user.id] = {"points" : 0, "messages" : 0, "cmduses" : 0, "claimed" : None, "rankimage" : None, "ranktext" : None, "rankaccent" : None}
        self.db.run(sql)

        self.db.commit()
        return  
    
    # Log_guild is to add individual guilds to our database.
    async def log_guild(self, guild):

        class fakeRole():

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
            logs =  False
        
        try:

            muterole = await self.fetch_mute_role(guild)
        
        except:

            muterole = fakeRole()
        
        prefix = 'b/'

        sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES ({guild.id},null,{logs},{muterole.id},'{prefix}',{logchan}) ON CONFLICT DO NOTHING"

        try:
            
            rows = self.db.run(sql)
        
        except:

            sql = f"INSERT INTO guilddata (guildid, adminroles, logs, muterole, prefix, logchannelid) VALUES ({guild.id}, null, {logs}, {muterole.id}, 'b/', 0 ) ON CONFLICT DO NOTHING"

            rows = self.db.run(sql)
    
        path = f"/media/home/FS2/WEB/blutopia.ca/img/blutonium/{guild.id}"
        if not os.path.exists(path):

            os.mkdir(path)
        
        self.db.commit()
        return

    # Set_owner is to add a user to the owners list.
    def set_owner(self,userid):

        sql = f"INSERT INTO owners (userid) VALUES ({userid}) ON CONFLICT DO NOTHING"

        self.db.run(sql)

        self.owner_cache.append(userid)
        self.owner_ids.append(userid)

        self.db.commit()

    # Remove_owner is to delete a user from the owners list.
    def remove_owner(self, userid):

        sql = f"DELETE FROM owners WHERE userid={userid}"

        self.db.run(sql)

        self.owner_cache.append(userid)
        self.owner_ids.append(userid)

        self.db.commit()         

    # Fetch_member is to get a member using the user command input.
    def fetch_member(ctx, inp):

        print(inp)

        member = None

        try:
            member = get(ctx.guild.members, id=int(inp))
                
        except:

            if inp:
                
                member = get(ctx.guild.members, name=inp)
                        
                if member is None:

                    member = get(ctx.guild.members, display_name=inp)
                
                if member is None:

                    bro = inp.split('#')

                    member = get(ctx.guild.members, name=bro[0], discriminator=bro[1] )

            if  inp is None:
                member : discord.Member = ctx.author
            else:
                for men in ctx.message.mentions:
                    member = men

        return member

    # Fetch_log_data is to fetch the logging settings from the cache.
    def fetch_log_data(self,guild):

        data = (guild.id, self.guild_cache[guild.id]["logsenabled"], self.guild_cache[guild.id]["logchannelid"])

        if data[2] == 0:
            
            chan = get(guild.channels, name='logs')

            if chan is None:
                chan = get(guild.channels, name='Logs')

            if chan is None:

                # make loggingfalse
                self.guild_cache[guild.id]["logsenabled"] = False

            else:

                # make the channel this new found channel
                self.guild_cache[guild.id]["logchannelid"] = chan.id
                
        return data    

    # Update_Log_channel is to change the channel that blutonium will log in a given guild
    def update_log_channel(self, guild, channelid):

        logdata = self.fetch_log_data(guild)

        sql = f"UPDATE guilddata SET logchannelid = {channelid} WHERE guildid = {guild.id}"

        self.db.run(sql)
        self.guild_cache[guild.id]['logchannelid'] = channelid

        self.db.commit()

        return 0

    # Toggle_logs is to toggle logging in a given guild
    def toggle_logs(self,guildid):

        enabled = self.guild_cache[guildid]['logsenabled']

        if enabled:

            sql  = f"UPDATE guilddata SET logs = False WHERE guildid = {guildid}"
            self.guild_cache[guildid]['logsenabled'] = False
            self.db.run(sql)
            self.db.commit()
            return 0 
        
        else:

            sql = f"UPDATE guilddata SET logs = True WHERE guildid = {guildid}"
            self.guild_cache[guildid]['logsenabled'] = False
            self.db.run(sql)
            self.db.commit()
            return 1

    # Fetch_simple_member fetches a member using the user input from the command but ths one only get's @mentions and user IDs no names or nicknames
    def fetch_simple_member(self, ctx, input):
        
        # set the user variable to None this means the method will return None if the fetch doesnt work
        user = None

        # try and get the user using the unput
        try:

            # we turn the input to an INT 
            input = int(input)

            user = get(ctx.guild.members, id=input)
        
        # when we get a Errror that means the user didnt input a ID
        except:

            # try and get the message mentions
            if ctx.message.mentions:
                # get the first mention
                user = ctx.message.mentions[0]
        
        # return the user
        return user 

    # Mute Is to add a mute to our cache and database
    def mute(self, guildid, userid, modid, reason, time):

        sql = f"INSERT INTO mutes (guildid, mutedid, reason, time, modid) VALUES ({guildid}, {userid}, '{reason}', '{time.strftime('%Y-%m-%d %H:%M:%S.%f')}', {modid}) ON CONFLICT DO NOTHING"

        self.db.run(sql)
        self.mute_cache[guildid][userid] = {'active':True,'modid':modid, 'reason':reason, 'time': time}

        self.db.commit()
    
    # Fetch Mutes is to get all he mutes in a given guild
    def fetch_mutes(self, guildid):

        sql = f"SELECT * FROM mutes WHERE guildid = {guildid}"

        rows = self.db.run(sql)

        return rows

    # fetch_active_mutes is essentially the same as fetch_mutes but this method querys our cache instead of our database so that our unmute loop can run faster.
    def fetch_active_mutes(self, guildid):

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
    def hackban(self, guildid, userid, reason):

        sql = f"INSERT INTO hackbans (guildid, userid, reason) VALUES ({guildid}, {userid}, '{reason}') ON CONFLICT DO NOTHING"
        
        self.db.run(sql)
        self.hackban_cache[guildid]['users'].append(userid)

        self.db.commit()

    # Unhackban is to delete a user from the hackban cache and datbase
    def unhackban(self, guildid, userid):

        sql = f"DELETE FROM hackbans WHERE userid={userid} AND guildid={guildid}"

        self.db.run(sql)
        self.hackban_cache[guildid]['users'].remove(userid)

        self.db.commit()
    
    # Fetch_hackbans is to get all the hackbans from a specific guild.
    def fetch_hackbans(self, guildid):

        sql = f"SELECT * FROM hackbans WHERE guildid={guildid}"

        rows = self.db.run(sql)

        self.db.commit()

        return rows


