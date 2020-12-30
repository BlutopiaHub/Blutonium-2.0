# import the necessary packages
from discord.ext import commands
from blutopia import Client


# define the cog class
class dbevents(commands.Cog, name="Dbevents"):

    # init code
    def __init__(self, client):

        # create our global client variable
        self.client: Client = client

        # create and run our db build method
        self.client.loop.create_task(self.build_database())

    # on_join_guild event
    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        # genereate database guild data
        await self.client.log_guild(guild)
        
    # on_member_join event
    @commands.Cog.listener()
    async def on_member_join(self, member):
        
        # generate our user data
        self.client.create_user(member)
        
    # method to add all data we didnt get while the bot was offline to the database
    async def build_database(self):

        # try and add all the missing data to the database
        try:

            # print some feed
            print("Adding new guilds and users to db...")

            # wait until the client caches and such are built
            await self.client.wait_until_ready()
            
            # generate our guild data for every guild
            await self.client.all_guilds_data_build()

            # generate our user data for every user
            self.client.all_users_data_build()

        # In the event of an exception, print the error message
        except Exception as err:

            # print our error
            print(f"Failed to generate saved data! {err}")
        
        # if all is well
        else:

            # print end feed
            print("Missing data successfully added!")
        
        self.client.loop.create_task(self.rebuild_caches())
    
    # a method to quickly rebuild all our caches
    async def rebuild_caches(self):

        # Try and rebuild all our caches
        try:

            print("Rebuilding caches...")

            self.client.build_caches()

        # In the event of an exception, print the error message
        except Exception as err:

            # print the error 
            print(err)
        
        # if all is well
        else:

            # print our feedback
            print("Caches successfully built!")


# setup function is called when the client loads the extension
def setup(client):
    client.add_cog(dbevents(client))
