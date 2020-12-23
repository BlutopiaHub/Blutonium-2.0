# import the necessary packages
import discord, os, datetime
from discord.ext import commands
from setup import OWNERID
from discord.utils import get
from client import Client

# define cog class
class sys(commands.Cog, name='System'):

    """
    Commands to manage the Client and do important things. 
    """

    # init code
    def __init__(self,client):

        # define the global client variable
        self.client : Client = client

    # reloadall command to reload all extensions
    @commands.is_owner()
    @commands.command(name='reloadall', aliases=['rlall', 'rla', 'restart'], help='Reload every extension')


    # load command to load extensions
    @commands.is_owner()
    @commands.command(name='load',aliases=['le', 'lo'], usage='`[Folder]` `[extension]`', help="Load an extension")
    async def _load(self,ctx,*args):
        
        # get all the extension direcdtories
        dirs = os.listdir('./extensions')
        
        # if the first arg is a directory in the extension directory...
        if args[0] in dirs:

            # Try and load the specidied extension in the directory
            try:

                # load
                self.client.load_extension(f'extensions.{args[0]}.{args[1]}')
                self.client.dispatch('extension_load', f'extensions.{args[0]}.{args[1]}',  datetime.datetime.now())
                # send feedback message
                await ctx.send(f'⬆ Successfully loaded extension `{args[1]}`')

            # in the event of an exception...
            except Exception as err:
                # Send a message with the error
                await ctx.send(f"Could not load extension `{args[1]}`: {err}")

        # if the subfolder doesnt exist
        else:
            # send a message that the subfolder doesnt exist
            await ctx.send(f"Could not find folder {args[0]}")

    # unload command to unload extensions
    @commands.is_owner()
    @commands.command(name='unload',aliases=['ule', 'ul'], usage='`[Folder]` `[extension]`', help="Unload an extension")
    async def _unload(self,ctx,*args):
        
        # get all the extension direcdtories
        dirs = os.listdir('./extensions')
        
        # if the first arg is a directory in the extension directory...
        if args[0] in dirs:

            # Try and unload the specified extension in the directory
            try:

                # unload
                self.client.unload_extension(f'extensions.{args[0]}.{args[1]}')
                
                # send success message
                await ctx.send(f'⬇ Successfully unloaded extension `{args[1]}`')
            
            # in the event of an exception...
            except Exception as err:
                # Send a message with the error
                await ctx.send(f"Could not unload extension `{args[1]}`: {err}")

        # if the subfolder doesnt exist
        else:
            # send a message that the subfolder doesnt exist
            await ctx.send(f"Could not find folder {args[0]}")

    # reload command to reload extensions
    @commands.is_owner()
    @commands.command(name='reload',aliases=['rl', 'rle'], usage='`[Folder]` `[extension]`', help="Reload an extension")
    async def _reload(self,ctx,*args):
        
        # get all the extension direcdtories
        dirs = os.listdir('./extensions')
        
        # if the first arg is a directory in the extension directory...
        if args[0] in dirs:

            # Try and reload the specified extension in the directory
            try:

                # unload
                self.client.unload_extension(f'extensions.{args[0]}.{args[1]}')

                # load
                self.client.load_extension(f'extensions.{args[0]}.{args[1]}')
                self.client.dispatch('extension_load',f'extensions.{args[0]}.{args[1]}', datetime.datetime.now())
                # send success message
                await ctx.send(f'🔁 Successfully reloaded extension `{args[1]}`')
                
            # in the event of an exception...
            except Exception as err:
                # Send a message with the error
                await ctx.send(f"Could not reload extension `{args[1]}`: {err}")

        # if the subfolder doesnt exist
        else:
            # send a message that the subfolder doesnt exist
            await ctx.send(f"Could not find folder {args[0]}")

    # the owners command group is to add and remove owners from the owner list *only the main owner can 
    @commands.is_owner()
    @commands.group(name='owner', aliases=['owners'])
    async def _owner(self,ctx):

        if ctx.invoked_subcommand is None:
            return

    # owner -> add subcommand
    @_owner.command(name='add', aliases=['append', 'new', 'set'])
    async def _add_owner(self,ctx,*args):

        # get the input after the sub command to find the user
        user = self.client.fetch_member(ctx," ".join(args[0:]))
        
        # if the user cant be found
        if user is None:

            # say that the user isnt found!
            return await ctx.send("User not found!")

        
        # if the user is already an owner
        if user.id in self.client.owner_cache:

            # tell em that
            return await ctx.send(f"User **{user}** is already an owner")

        # add the owner
        self.client.set_owner(user.id)

        # send the feedback
        await ctx.send(f"Added **{user}** as an owner ({user.id})")

    # owner -> remove subcommand
    @_owner.command(name='remove', aliases=['rem', 'del', 'unset', 'delete'])
    async def _rem_owner(self,ctx,*args):
        

        # get the input after the sub command to find the user
        user = self.client.fetch_member(ctx," ".join(args[0:]))
        
        # if the user cant be found
        if user is None:

            # say that the user isnt found!
            return await ctx.send("User not found!")

        # if the user is not an owner
        if user.id not in self.client.owner_cache:

            # tell em that 
            return await ctx.send(f"User **{user}** is not an owner")

        # remove the owner
        self.client.remove_owner(user.id)

        # send feedback
        await ctx.send(f"Removed **{user}** as an owner ({user.id})")

# setup function is called when the client loads the extension  
def setup(client):

    cog = sys(client)

    client.add_cog(cog)