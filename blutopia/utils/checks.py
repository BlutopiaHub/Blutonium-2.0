from discord.ext import commands


# has adminrole is a permission checker that will be on some commands
def has_adminrole(ctx: commands.context):
    allow = False

    for role in ctx.author.roles:

        if role.id in ctx.bot.fetch_adminroles(ctx.guild.id):
            allow = True

    return allow
