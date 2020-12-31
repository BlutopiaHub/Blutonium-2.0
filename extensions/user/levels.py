import discord
import requests
import os
import datetime

from discord.ext import commands
from discord.utils import get
from io import BytesIO
from blutopia import Client
from PIL import Image, ImageDraw, ImageOps, ImageFont
from purgo_malum import client as purgoclient


class levels(commands.Cog, name='Levels'):

    def __init__(self, client):
        self.client: Client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        ctx: commands.Context = await self.client.get_context(message)

        if ctx.valid:

            if ctx.command:
                return

        self.client.leveluser(message.author.id, message.guild.id)

    @commands.command()
    async def rank(self, ctx: commands.Context, *, user=None):

        support = get(self.client.guilds, id=629436501964619776)
        emoji = get(support.emojis, name="Blutonium_loading")
        emoji2 = get(support.emojis, name="BlutoX")
        emb = discord.Embed(title=f'{emoji} Generating rank card...')

        msg = await ctx.send(embed=emb)

        colors = (('green', '#27d600'), ('blue', '#0064d6'),
                  ('red', '#e30000'), ('white', '#ffffff'),
                  ('black', '#000000'), ('gold', '#ffd500'),
                  ('pink', '#ff75fa'), ('purple', '#8400ff'))

        if user is None:
            user = ctx.author
        else:
            user = self.client.fetch_simple_member(ctx, user)

        leveldata = self.client.levels_cache[ctx.guild.id][user.id]
        userdata = self.client.fetch_user_data(user.id)

        rankimage = userdata['rankimage']
        ranktext = userdata['ranktext']
        accent = userdata['rankaccent']

        masksize = (700, 700)
        mask = Image.new('L', masksize, 0)

        Maskdraw = ImageDraw.Draw(mask)
        Maskdraw.ellipse((0, 0) + masksize, fill='#fff')

        mask = ImageOps.fit(mask, (160, 160))

        aurl = '.'.join(str(user.avatar_url).split('.')[:3]) + '.png'

        pfp = requests.get(aurl)
        link = rankimage

        TINT_COLOR = (0, 0, 0)
        TRANSPARENCY = .60
        OPACITY = int(255 * TRANSPARENCY)

        if accent is None:
            accent = '#FFF'

        for x in colors:

            if accent == x[0]:
                accent = x[1]

        try:
            image = requests.get(link)
        except:
            image = requests.get('https://img.wallpapersafari.com/desktop/1920/1080/89/4/6KjDH9.jpg')

        profile = Image.open(BytesIO(pfp.content))
        circular = ImageOps.fit(profile, mask.size)
        circular.putalpha(mask)

        circular = circular.convert('RGBA')
        image = Image.open(BytesIO(image.content))
        image = ImageOps.fit(image, (700, 200))

        rec = Image.new('RGBA', image.size, TINT_COLOR + (0,))
        drew = ImageDraw.Draw(rec)
        drew.rectangle((10, 10, 690, 190), fill=TINT_COLOR + (OPACITY,))

        image = image.convert('RGBA')
        image = Image.alpha_composite(image, rec)

        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype(os.path.join('fonts', 'arial.ttf'), 32)
        font2 = ImageFont.truetype(os.path.join('fonts', 'arial.ttf'), 18)
        font3 = ImageFont.truetype(os.path.join('fonts', 'arial.ttf'), 25)

        image.paste(circular, (20, 20, 180, 180), mask=mask)
        draw.text((200, 50), f'{user}', align='center', font=font, fill=accent)

        text = ranktext

        if text is None:
            text = " "

        text = purgoclient.retrieve_filtered_text(text)

        draw.text((200, 85), f'{text}', align='center', font=font3, fill=accent)

        draw.text((548, 145), f'{leveldata["currentxp"]} / {leveldata["requiredxp"]}xp', align='center', font=font2, fill=accent)
        draw.text((200, 145), f'Level {leveldata["currentlevel"]}', align='center', font=font2, fill=accent)

        recbox = (200, 120, 630, 140)

        levelpercentage = round(((leveldata["currentxp"] / leveldata["requiredxp"]) * 100))

        fill = ((levelpercentage * 430) / 100) + 200

        recboxfill = (200, 120, fill, 140)
        draw.rectangle(recbox)
        draw.rectangle(recboxfill, fill=accent)

        path = f"/media/home/FS2/WEB/blutopia.ca/img/blutonium/{ctx.guild.id}/{user.id}.png"
        image.save(path, format='PNG')

        link = f'http://localhost/img/blutonium/{ctx.guild.id}/{user.id}.png'

        req = requests.get(link)

        img = BytesIO(req.content)
        img.name = f"{user.id}.png"

        file = discord.File(img)

        await msg.delete()
        await ctx.send(file=file)

    @commands.group(name='rankcard', aliases=['rc'])
    async def _rankcard(self, ctx):

        if ctx.invoked_subcommand is None:

            accent = self.client.user_cache[ctx.author.id]['rankaccent']
            prefix = self.client.fetch_prefix(ctx.guild.id)
            text = self.client.user_cache[ctx.author.id]['ranktext']

            if text is None:
                pass
            else:
                text = purgoclient.retrieve_filtered_text(text)

            bg = self.client.user_cache[ctx.author.id]['rankimage']

            emb = discord.Embed(title=f'{ctx.author} rank card configuration',
                                timestamp=datetime.datetime.utcnow(),
                                colour=0x36393F)

            emb.add_field(name='Background',
                          value=f'\n**Current:** {bg}\n**Usage:** {prefix}rankcard --background [img link]',
                          inline=False)

            emb.add_field(name='Accent Color',
                          value=f'\n**Current:** {accent}\n**Usage:**'
                                f' {prefix}rankcard --accent [color]\n'
                                f' leave the color blank to see all the options',
                          inline=False)

            emb.add_field(name='Custom Text',
                          value=f'\n**Current:** {text}\n**Usage:**'
                                f' {prefix}rankcard --text [text]',
                          inline=False)

            emb.set_thumbnail(url=ctx.author.avatar_url)

            await ctx.send(embed=emb)

    @_rankcard.command(name='background', aliases=['bg'])
    async def _rankcard_background(self, ctx, link):

        self.client.set_rankbg(ctx.author.id, link)

        await ctx.send('Successfully set background')

    @_rankcard.command(name='accent', aliases=['acc'])
    async def _rankcard_accent(self, ctx, accent):

        colors = ['green', 'blue', 'red', 'white', 'black', 'gold', 'pink', 'purple']

        try:

            if accent.startswith('#'):
                if len(accent) > 7:
                    return await ctx.send('Invalid HEX code')

                if len(accent) < 7:

                    if len(accent) == 4:
                        pass
                    else:
                        return await ctx.send('Invalid HEX code')

                self.client.set_accent(ctx.author.id, accent)

                return await ctx.send('Accent color successfully changed')

            elif accent.lower() in colors:

                self.client.set_accent(ctx.author.id, accent)

                return await ctx.send('Accent color successfully changed')

            else:
                raise KeyError

        except Exception:

            return await ctx.send(f'Invalid color! Options are ``{", ".join(colors)} `` or a HEX code')

    @_rankcard.command(name='text', aliases=['txt', 'bio'])
    async def _rankcard_text(self, ctx, *, text):

        if len(text) > 30:
            return await ctx.send("text too long")

        self.client.set_ranktext(ctx.author.id, text)

        return await ctx.send('Text successfully changed')

    @commands.command(name='levels', aliases=['levelboard', 'lblevel'])
    async def _levels(self, ctx, glbl=None):

        # if glbl is None then set glbl to false
        if glbl is None:
            glbl = False

        if glbl == 'global':
            glbl = True

        # get the levels database
        lb = self.client.fetch_level_leaderboard(ctx.guild.id, glbl)

        # create our leaderboard embed
        if glbl:

            emb = discord.Embed(title=f'Global levels leaderboard',
                                timestamp=datetime.datetime.utcnow(),
                                color=0x2F3136)
            emb.set_thumbnail(url='https://proxy.blutopia.ca/img/blutonium.png')

        else:

            emb = discord.Embed(title=f'{ctx.guild} levels leaderboard',
                                timestamp=datetime.datetime.utcnow(),
                                color=0x2F3136)
            emb.set_thumbnail(url= ctx.guild.icon_url)

        entrynum = 1

        for entry in lb:

            # define our variables to put in the leaderaboard
            userid, currentlevel, currentxp, requiredxp = entry[0], entry[1], entry[2], entry[3]

            # get our user
            user = self.client.fetch_member(ctx, userid)

            # get an emoji we need
            dashemoji = get(self.client.emojis, name='purple_dash')

            user = user.mention if user is not None else userid

            emb.add_field(name=f'#{entrynum} {dashemoji} **Level {currentlevel} | {currentxp}/{requiredxp}xp**\n',
                          value=f"{user}",
                          inline=False)

            entrynum += 1

        await ctx.send(embed=emb)
"""
            if user is None:
                error = 'User not found!'
            else:
                error = err

            emb = discord.Embed(title=f'{emoji2} Rank card Failed: {error}')
            await msg.edit(embed=emb)
"""


def setup(client):
    client.add_cog(levels(client))
