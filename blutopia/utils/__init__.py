import requests
from blutopia.setup import TOKEN
import discord
import datetime
import humanize as h
from blutopia import setup as s
import operator


# Define our static methods that we will be using within our commands, but can also be used outside of the class.
# chop_microseconds will be used to remove microseconds from a datetime object
def chop_microseconds(delta):
    return delta - datetime.timedelta(microseconds=delta.microseconds)


# request_song_info is to get the link for genius lyrics of a song
def request_song_info(song, artist):
    # define the base url of the request
    base_url = 'https://api.genius.com'

    # define the headers of the web request
    headers = {'Authorization': 'Bearer ' + s.geniuskey}

    # define our search url
    search_url = base_url + '/search'

    # setup the query for the search
    data = {'q': song + ' ' + artist}

    # request the data from the genius api
    response = requests.get(search_url, data=data, headers=headers)

    # return the response from the server
    return response


# make a method called checkfornitro. This checks if the user's avatar is animated and also checks if the
# user has a nitro booster role
def checkfornitro(target):
    # we will start assuming the user has no nitro
    isnitro = False

    # if the user has an animated avatar
    if target.is_avatar_animated():
        # set nitro to True
        isnitro = True

    # if the user has a nitro boost role
    if "nitro booster" in [role.name.lower() for role in target.roles]:
        # set nitro to True
        isnitro = True

    return isnitro


# this method is made to check the guild join position of the user
def find_joinpos(target, guild):
    # We will try catch this in case we get an unexpected error,
    # we still want to be able to display the user info
    try:

        # get all the joins in the guild
        joins = tuple(sorted(guild.members, key=operator.attrgetter('joined_at')))

        # if theres any NoneTypes in the joins tuple were not going to deal with this
        if None in joins:
            # return a Nonetype
            return None

        # for every user in the joins tuple
        for joinkey, elem in enumerate(joins):

            # if the user is == to the target
            if elem == target:
                # return the joinkey and the total ammount of joins
                return joinkey + 1, len(joins)

        # if none these if statements are ran, we get here and we just return a Nonetype
        return None

    # in the event of an error
    except Exception as err:

        # print the error
        print(err)

        # return a NoneType
        return None


# guild embed method
def guildembed(guild):
    # initialize the embed
    embed = discord.Embed(title=f'{guild}', colour=discord.Colour.blue(), timestamp=datetime.datetime.now())

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
    embed.add_field(name='Text channels', value=TextChs, inline=True)

    # set the embed categories field
    embed.add_field(name='categories', value=catcount, inline=True)

    # Set the embed region field
    embed.add_field(name='Region', value=f'{guild.region}', inline=True)

    # Set the embed voice channels field
    embed.add_field(name='Voice channels', value=voiceChs, inline=True)

    # Set the server id field
    embed.add_field(name='Server ID', value=f'{guild.id}', inline=True)

    # Set the server owner field
    embed.add_field(name='Server owner', value=f'{guild.owner}', inline=True)

    # Set the total members field
    embed.add_field(name='total members', value=len(guild.members), inline=True)

    # Set the total humans field
    embed.add_field(name='humans', value=membercount, inline=True)

    # Set the total bots field
    embed.add_field(name='bots', value=botcount, inline=True)

    # Set the guild created field
    embed.add_field(name='Created', value=f'{h.naturaltime(guild.created_at)}', inline=True)

    # Set the roles field
    embed.add_field(name='roles', value=roles)

    # Set the embed thumbnail
    embed.set_thumbnail(url=servericonurl)

    # return the whole embed
    return embed


def request_discord_user(userid):
    base_url = 'https://discord.com/api/v8'
    headers = {'Authorization': 'Bot ' + f'{TOKEN}'}
    search_url = base_url + f'/users/{userid}'
    response = requests.get(search_url, headers=headers)

    return response
