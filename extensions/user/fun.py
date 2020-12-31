# import the nessecary modules

import discord
import datetime
import requests

from discord.ext import commands
from discord.utils import get
from blutopia import Client
from blutopia.utils import request_discord_user
from random import randrange

import humanize as h


# define our main Cog class
class Fun(commands.Cog, name="Fun"):
    """
    Fun commands for messing with friends and having a good time.
    """

    # init code
    def __init__(self, client):

        # define our global client variable
        self.client: Client = client

        # initialize our global emote variables
        self.support = ''
        self.checkemoji = ''
        self.crossemoji = ''
        self.dashemoji = ''
        self.blutonium = ''

        # create the task for getting the emojis
        client.loop.create_task(self.getEmojis())

    # Define our class methods
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
    
    # Meme command is to fetch a random meme from reddit
    @commands.cooldown(rate=1, per=10)
    @commands.command(name='meme', aliases=['m'],
                      help='Fetch a random meme from reddit.')
    async def _meme(self, ctx):
        
        # request a meme from our meme api
        request = requests.get('https://apis.duncte123.me/meme')
        
        # get the json from the request
        json = request.json()
        
        # create our embed
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(),
                              title='Quality meme',
                              url=json['data']['url'])

        # add our image to the embed
        embed.set_image(url=json['data']['image'])

        # send the embed
        await ctx.send(embed=embed)

    # Boop command to boop someone
    @commands.command(name='boop', aliases=['bab', 'bop'],
                      help='Boop someone.', usage='`[userid, name, or mention]`')
    async def _boop(self, ctx: commands.Context, *, inp=None):

        # get the alias that was used to invoke this command
        alias = ctx.invoked_with

        # if the input is None then we ask then to input a user to boop
        if inp is None:

            # send the error message
            return await ctx.send(f"{self.crossemoji}**Please input a user to {alias}**")

        # get the user using the input
        user = self.client.fetch_member(ctx, inp)

        # if the authors top role is under the target's top role
        if ctx.author.roles[-1].position < user.roles[-1].position:

            # the author has no permission to bab the target so send an error
            return await ctx.send(f"{self.crossemoji}**You dont have permission to bab this user**")

        # if the user is the author we wont allow the to boop themselves
        if user == ctx.author:

            # send the error message
            return await ctx.send(f"**{self.crossemoji}Thou shall not {alias} thyself**")

        # after all the checks are over we will boop the user
        await ctx.send(f"{self.checkemoji}**{user} was successfully {alias}ed**")

    # Points command is to see how many points you have
    @commands.command(name='points', aliases=['balance', 'bal'],
                      help='Show how many points you have.', usage='`<args>`')
    async def _points(self, ctx, *args):

        # get the current points
        points = self.client.fetch_points(ctx.author.id)

        # if the points is None then they have no points
        if points is None:

            # return that we have no points
            return await ctx.send("**You have ``0`` points**")

        # try and get the args
        try:
            # if the --half arg is present
            if '--half' == args[0]:

                # split the points in half
                points = points/2

            # if the --quart arg is present
            elif '--quart' == args[0]:

                # split the points in a quarter
                points = points/4

            # if the --eighth arg is present
            elif '--eighth' == args[0]:

                # split the points in an eighth
                points = points/8

        # if we get a IndexError there are no args
        except IndexError:

            # continue on
            pass

        # lastly we will convert the points to INT to make sure there are no decials
        points = int(points)

        await ctx.send(f"**You have ``{points}`` points**")

    # Gamble command is to gamble all your points away
    @commands.command(name='gamble', aliases=[],
                      help='Help feed your gambling addiction', usage='`[ammount]`')
    async def _gamble(self, ctx, ammount):

        # get the user that is gambling
        user = ctx.author

        # get the user's points
        startingpoints = int(self.client.fetch_points(user.id))

        # create the 50% chance
        chance = randrange(0, 2)

        # if the ammount input is "all" then we want to gamble all of our points
        if ammount.lower() == 'all':
            ammount = startingpoints

        # if ammount input is "half" then we want to gamble half of our points
        elif ammount.lower() == 'half':
            ammount = startingpoints/2

        # if ammount input is "quart" then we want to gamble a quarter of our points
        elif ammount.lower() == 'quart':
            ammount = startingpoints/4

        # if ammount input is "eighth" then we want to gamble am eighth of our points
        elif ammount.lower() == 'eighth':
            ammount = startingpoints/8

        # finally we convert our ammount to int to remove any decimals
        ammount = int(ammount)

        # now we will perform all of our checks
        # if the ammount is 0 we will cancel this because you cant gamble 0 points
        if ammount == 0:
            return await ctx.send(f'{self.crossemoji}**You can\'t gamble 0 points!')

        # if the ammount is more then the points we have we cant afford this gamble
        if ammount > startingpoints:
            return await ctx.send(f"{self.crossemoji}**You can't afford that gamble!")

        # if the ammount is less than 0 we dont want that either as it will cause issues in the math
        if ammount < 0:
            return await ctx.send(f"{self.crossemoji}**You can't gamble negative points, silly.")

        # now we will do our 50/50 split
        if chance:

            # set our new points variable to ammount + starting points since we won.
            newpoints = ammount + startingpoints

            # if the ammount is the same as the starting points that means we went all in!
            if ammount == startingpoints:
                await ctx.send(f"**You went all in and WON! You now have ``{newpoints}`` points.**")

            # if its not the same we send a normal feedback
            else:
                await ctx.send(f"**You gambled ``{ammount}`` points and WON! You now have ``{newpoints}`` points.**")

        # if chance is false that means we lost
        else:

            # set our new points ammount - startingpoints since we lost
            newpoints = startingpoints - ammount

            # if the ammount is the same as the starting points that means we went all in!
            if ammount == startingpoints:
                await ctx.send(f"**You went all in and lost everything LMAO. You now have ``{newpoints}`` points.**")

            # if its not the same we send a normal feedback
            else:
                await ctx.send(f"**You gambled ``{ammount}`` points and lost them all."
                               f" You now have ``{newpoints}`` points.**")

        # set our new points
        self.client.set_points(user.id, newpoints)

    # Set points for owner to set someone elses points
    @commands.is_owner()
    @commands.command(name='setpoints', aliases=[],
                      help='Set a user\'s points')
    async def _setpoints(self, ctx, ammount, *, user=None):

        # get the user using the input
        user = self.client.fetch_member(ctx, user)

        # try and convert the ammount to an INT
        try:

            # covert to int
            int(ammount)

        # if we get an error the user didnt input a valid number
        except TypeError:

            # send the error message
            return await ctx.send(f'{self.crossemoji}**Please input a valid number to set for points**')

        # set the points for the user
        self.client.set_points(user.id, ammount)

        # send the feedback
        await ctx.send(f"{self.checkemoji}**Sucessfully set {user} to ``{ammount}`` points**")

    # reset for owner to reset a user's points
    @commands.is_owner()
    @commands.command(name='reset', aliases=['delpoints'],
                      help='Reset a user\'s points')
    async def _reset(self, ctx, *, user=None):

        # get the user using the input
        user = self.client.fetch_member(ctx, user)

        # set the points to zero
        self.client.set_points(user.id, 0)

        # send the feedback
        await ctx.send(f'**Successfully reset {user}**')

    # daily for claiming daily points
    @commands.command(name='daily', aliases=[],
                      help='Claim your daily points')
    async def _daily(self, ctx):

        # use the fetch claimed method
        isClaimed = self.client.fetch_claimed(ctx.author.id)

        # if our fetch claimed method returns false that means they cannot claim right now
        if not isClaimed[0]:

            return await ctx.send(f'**You can claim your daily points again in ``{h.precisedelta(isClaimed[1])}``**')

        # if our method returns true give them 100 points
        else:

            points = self.client.fetch_points(ctx.author.id)
            points = points + 100

            self.client.set_points(ctx.author.id, points)

            await ctx.send("**You have claimed your daily 100 points!**")

    # gift to give someone some points
    @commands.command(name='gift', aliases=['giftpoints', 'givepoints', 'give'],
                      help='Give some points to another user!')
    async def _gift(self, ctx, ammount, *, user=None):

        # if the user arg is None the user didnt inpt any user to give points to
        if user is None:

            # send error
            return await ctx.send(f"{self.crossemoji}**Please input a user to give points to.**")

        # connvert ammount to Int if we et an errr it means they didnt input a valid number
        try:
            ammount = int(ammount)
        except ValueError:
            return await ctx.send(f"{self.crossemoji}**Please input a valid ammount of points to give**")

        # get the user using the input
        user = self.client.fetch_member(ctx, user)

        # get the gifter's points
        gifterpoints = self.client.fetch_points(ctx.author.id)

        # get the recipient's points
        recipientpoints = self.client.fetch_points(user.id)

        # perform all of our checks
        # if rhe recipient is the author end this command
        if user.id == ctx.author.id:
            return await ctx.send(f"{self.crossemoji}**You can't gift points to yourself**")

        # if the givters points is less than the ammount they want to give they can't afford this transction
        if gifterpoints < ammount:
            return await ctx.send(f"{self.crossemoji}**You can't afford that transaction!**")

        # if the ammount is 0 we cant do this
        if ammount == 0:
            return await ctx.send(f"{self.crossemoji}**You can't gift 0 points**")

        # if the ammount is less than 0 we cant do that
        if ammount < 0:
            return await ctx.send(f"{self.crossemoji}**You can't gift negative points, silly.**")

        # Try and perform the transaction
        try:

            # set the gifter's new points
            gifternewpoints = gifterpoints - ammount
            self.client.set_points(ctx.author.id, gifternewpoints)

            # set the recipients new points
            recipientnewpoints = recipientpoints + ammount
            self.client.set_points(user.id, recipientnewpoints)

        # if we get some kind of error revert the changes
        except Exception as err:

            # print the error
            print(err)

            # revert the changes
            self.client.set_points(ctx.author.id, gifterpoints)
            self.client.set_points(user.id, recipientpoints)

            # send the error message
            await ctx.send(f"{self.crossemoji}**Transaction failed!**")

        # if we get no errors
        else:

            # send feedback
            await ctx.send(f"{self.checkemoji}**Transaction sucessful! "
                           f"{ctx.author} now has ``{gifternewpoints}`` points.**")

    # leaderboard is to get the leaderboard of points in the guild
    @commands.command(name='leaderboard', aliases=['toppoints', 'lb'],
                      help='Get the leaderboard of points for the guild')
    async def _leaderboard(self, ctx):

        # get the leaderboard for the guild
        lb = self.client.fetch_guild_points_leaderboard(ctx.guild.members)

        # create an embed with for our leaderboard
        emb = discord.Embed(title=f'{ctx.guild} points leaderboard',
                            timestamp=datetime.datetime.utcnow(),
                            color=0x2F3136)

        # set the starting number for the leaderboard
        lbnum = 1

        # for every entry in the leaderboard
        for x in lb:

            # get the user
            user = self.client.fetch_member(ctx, x[0])

            # add the field for the embed
            emb.add_field(name=f'#{lbnum} - {user}',
                          value=f"{self.dashemoji}`{x[1]}` Points",
                          inline=False)

            # add 1 to the number
            lbnum += 1

        # send the embed
        await ctx.send(embed=emb)

    # ERROR HANDLERS
    @_meme.error
    async def on_meme_error(self, ctx, error):

        # if the error is a commands.errors.CommandOnCooldown that means that they have to wait the cooldown
        if isinstance(error, commands.errors.CommandOnCooldown):

            # get the ammount of cooldown left and round it
            cooldown = round(error.retry_after, 2)

            # send an error message
            await ctx.send(f"{self.crossemoji}**Command is on cooldown! Try again in ``{cooldown}`` seconds**")

        # if we get some kind of other error
        else:

            # print the error
            print(error)


def setup(client):
    client.add_cog(Fun(client))
