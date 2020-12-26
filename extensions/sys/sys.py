# import the necessary packages
from collections import defaultdict
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

        # define a global result dict for the restart command this is that so we can get back the latest results after the client reloaded
        self.latest_result_dict = {}

    # reloadall command to reload all extensions
    @commands.is_owner()
    @commands.command(name='reloadall', aliases=['rlall', 'rla', 'restart'], help='Reload every extension')
    async def _restart(self, ctx):
        
        # create a dict that will contain the extensions what directory theyre from and wether they failed or suceeeded. This will be used for our final feedback
        result_dict = defaultdict(dict)

        # create 2 objects that contain the number of failed exts and the number of success ext this will be used to determine the precentage of extensions that were sucessfully loaded
        success = 0
        failed = 0

        # get all the extension directories
        dirs = os.listdir('./extensions')

        # send a messages saying that were starting to load every extension, we will edit this message as we go adding which extensions were successfully loaded
        msg = await ctx.send(f"**Reloading extensions...**")

        # create a blacklist of directories we dont want to reload the extensions in
        dir_blacklist = ['proc']

        # for every extension directory
        for dir in dirs: 

            # if the directory is in the directory blacklist then continue to the next dir
            if dir in dir_blacklist:
                
                # continue statments stops this iteration of the loop and continues to the next one
                continue

            # edit the message and add which extension folder were at
            await msg.edit(content=f'**Reloading {dir} extensions...**')

            # get all the extensions in the diretory 
            # this only gets every file that ends with '.py'
            exts = [x.split('.py')[0] for x in os.listdir(f'./extensions/{dir}') if x.endswith('.py')]

            # for every extension in the directory
            for ext in exts:
                
                # get the official name of the extension
                ofc_ext = f'extensions.{dir}.{ext}'

                # if the extension is loaded
                if ofc_ext in self.client.extensions: 

                    # add the extension to our feedback message
                    msgcontent = msg.content + f"\n{ext}"

                    # edit the messsage
                    await msg.edit(content=msgcontent)

                    # try to reload the extension
                    try: 

                        # reload the extension
                        self.client.reload_extension(ofc_ext)
                        
                    
                    # if we get an error
                    except Exception as err:

                        # add that the reload failed to the message
                        msgcontent = msg.content + f" `FAILED`"

                        # edit the message
                        await msg.edit(content=msgcontent)

                        # add our ext to the result dict as a failed extension
                        result_dict[dir][ext] = {'result': False, 'error': err }

                        # add a fail to the ammount of extensions we failed to load
                        failed +=1
                    
                    # if we dont get an error
                    else:

                        # add that the reload was sucessful to the message
                        msgcontent = msg.content + f" `SUCCESS`"

                        # edit the message
                        await msg.edit(content=msgcontent)
                        
                        # add our ext to the result dict as a succeessful extension
                        result_dict[dir][ext] = {'result': True}

                        # add a sucess to the number of ext we sucessfully loaded
                        success += 1

        # get the total ammount of exts we loaded
        totalexts = success + failed

        # get the percetage of exts taht were sucessfully loaded
        percentage = (100*success)/totalexts

        # This method takes the percentage and blends Red and Green according to that percentage, the method will then turn that rgp color into a hex color.
        # This is used to decide the color of the success embed, for example if only 50% of the exts load corrrectly the color of the embed will appear yellow
        def convertpercentage(perc):

            # set our intiial red value
            r = 255

            # set our initial green value
            g = 255

            # our blue will stay at 0 since we arent blending this value
            b = 0

            # if the percentage of blend is under 50
            if perc < 50:
                
                # multiply it by 2
                # this is done because we basically are trying to find out what percentage of 225 we need for the color blend
                entage = perc*2

                # get {entage} percent of 225
                g = int((entage*255)/100)

            # if the percentage of the blend is 50, we already know that 50% blend is 225,255
            if perc == 50:

                pass
            
            # if the percentage of the blend is over 50
            if perc > 50:

                # subtract 50 from the percentage then multiply it by 2
                entage = (perc-50)*2

                # get {entage} percent of 225 and subtract it from our initial red value
                r -= int((entage*255)/100)

            # convert our final color to hex
            return '0x%02x%02x%02x' % (r,g,b)

        # Create our final feedback embed
        emb = discord.Embed(title='Restart results', description=f'{success}/{totalexts} extensions were loaded sucessfully. {percentage}%', color=discord.Colour(value=int(convertpercentage(percentage), 16)))

        # for every key in the result dict (every key would be each directory in this case)
        for dirkey in result_dict:
            
            # initialise the string that will contain all our results
            results = ''

            # for every key in this dir (in this case the keys would be every extesnion)
            for extkey in result_dict[dirkey]:

                # if the result key fot that extension = True then the extension was sucessfuly loaded
                if result_dict[dirkey][extkey]['result']:

                    # add a success to the results string
                    results += f'{extkey} `SUCCESS`\n'
                
                # if the result key for that ext is not True that means the ext failed
                else:

                    # add a fail to the result string
                    results += f"{extkey} `FAILED`\n"

            # if there are no results skip this iteration
            if results == '':

                # skip
                continue

            # create a field in our embed for this directory
            emb.add_field(name=f'{dirkey.capitalize()} extensions', value=results, inline=False)

        # edit our message and add the embed
        await msg.edit(content='**Restart Finished!**')
        await ctx.send(embed=emb)

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