# Blutonium Update 2.1.0 Changelog

## ADDITIONS

### Voice chat leveling! 
- Every minute in voice chat, you will be issued some XP
- The xp for voice chat is lower than xp for text chat
- The xp will not be issued if the user is muted, server muted, afk, deafened, or server deafened.
- Voice chat xp and Text chat xp are on the same timer. This means that if you just recieved XP for chatting in text chat and then right after another minute in vc pases, you will not recieve that VC xp because you are on cooldown for your chat xp.

### Warn autobans!
- After the ammount of warns a user has exceeds or is equal to the `maxwarns` config option the user will be automatically banned.


## UPDATES
- None

## FIXES
- Fixed a bug where the bot would not log when a user joined a voice channel.
- Fixed a big where literally nothing, was an alias for `userinfo`.

## IMPROVMENTS
- Moved some methods and classes into `blutopia/utils`.

## REMOVALS
- None

# PLEASE REPORT ANY BUGS YOU FIND! Thank you for supporting blutonium!