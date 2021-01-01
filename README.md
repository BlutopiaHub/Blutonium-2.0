#Blutonium Update 2.0.0 Changelog

##ADDITIONS
- Warning system. This includes the commands b/warn b/warns b/warn-remove and b/warns-given. After a set amount of warns, the user can be auto-banned, if the setting is enabled.
- Hackbanning. b\hackban b\unhackban. Prematurely ban someone who isn't in the server. As soon as they join they will be banned.
- More options in Config, b\config autoban and b\config maxwarns. You can set whether a user is auto-banned after an amount of warns. This amount is set by maxwarns and the banning is toggled with autoban.
- b\mutelist command see all the active mutes in the guild.
- b/dev tempcmd to write code from inside of discord.
- Added some new messages when starting up the bot.

##UPDATES
- Updated b\mute. Muting is now always a temporary mute. But you can still mute people for hundreds of years (literally).
- Updated b\minecraft. The Minecraft command was split into subcommand now, there are 6 subcommand server hypixel head body avatar and player.
- Head and body show a 3d view of the Minecraft user's head and body. You can also add arguments to the command --size, --nohelm, --left. --size will of course change the size desired. --nohelm removes the Minecraft "helmet" from the skin. And --left will make the 3d body or head be facing left.
- Avatar and Player will show a 2d view of the skin's head or body respectively. they have the same args besides --left because they are 2D. 
- Hypixel fetches a user's hypixel stats from the hypixel API.
- Server fetches info on any online Minecraft server.
- b\snipe is now per channel and has the time deleted in the embed. 
- b\avatar, b\servericon and b\enlarge now will work a lot better as the bot will download the image and send it as a file now.
- just running b/cfg without a subcommand now shows all the settings available and what they're set to.
- Split the b\rankcard command into subcommands instead of using *args

##FIXES
- Users can no longer ban/kick/mute other users with top roles that are above or equal to them. 
- Various python syntax issues fixed.
- Fixed an issue where new users would bot be added to the levels database or the userdata database.
- Fixed an issue where the bot would try to log anyways even when logging was disabled.
- Fixed some bad SQL choices for datatypes

##IMPROVMENTS
- Added caching to all stored data. This allows for way faster operation and makes the bot less intensive on the database. In Blutonium 1.17 the bot would fetch the prefix from a guild for every message in the database, it now gets it from it's internal cache. The bot will be hitting the database ALOT less now.
- Made the bot have a constant connection to the database instead of one that disconnects and reconnects every time it wants to get a piece of data.
- Updated almost every embed, embeds should look a lot cooler now Cool
- Added a custom class that subclasses comamnds.Bot this allowed for cleaner code in general.
- Made a python module to organize custom methods and classes. 
- Made presences in a commands.loop method instead of in on_ready.
- all extensions are organized into much easier to manage "modules" user, temp, sys, proc, loop, and event. 

##REMOVALS
- Removed b\pp
- Removed b\hypixel
- Removed adminroles database table and added the admin roles to guilddata
- Removed custom dispatches for load_extension and unload_extension, previously these custom events were used to cache extension uptimes, but that caching is built into the custom Client class now.
 

#PLEASE REPLY WITH ANY BUGS YOU FIND! Thank you for supporting blutonium!
