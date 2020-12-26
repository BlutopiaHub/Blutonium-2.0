# import the required packages
import os
import setup
import sys

from client import Client

# print some useful info
print(f"\nBlutonium Client v{setup.clientVer}")
print(f"Running python v{sys.version}\n")
print("Starting init process...\n")

# get all the sys extensions
sysexts   = [x.split('.py')[0] for x in os.listdir('./extensions/sys') if x.endswith('.py')]

# get all the user extensions
userexts  = [x.split('.py')[0] for x in os.listdir('./extensions/user') if x.endswith('.py')]

# get all the event extensions
eventexts = [x.split('.py')[0] for x in os.listdir('./extensions/event') if x.endswith('.py')]

# get all the loop extensions
loopexts = [x.split('.py')[0] for x in os.listdir('./extensions/loop') if x.endswith('.py')]


# this function runs with the client passed in. This way we can use our client variable while loading the extension
def setup(client: Client):

    # for all all the sys extensions (we need to load these first!!)
    for ext in sysexts:
        # try and load the extension
        try:
            client.load_extension(f'extensions.sys.{ext}')
        
        # print console feedback
            print(f'Extension {ext} was loaded successfully')
        
        # in the event of an exception
        except Exception as err:

            # print the error to console
            print(f'Extension {ext} could not be loaded {err}')

    # for all the command extensions
    for ext in userexts:
        
        # try and load the extension
        try:
            client.load_extension(f'extensions.user.{ext}')

        # print feedback to the console
            print(f'Extension {ext} was loaded successfully')

        # in the event of an exception
        except Exception as err:

            # print the error to console
            print(f'Extension {ext} could not be loaded {err}')

    # for all all the event extensions
    for ext in eventexts:
        # try and load the extension
        try:
            client.load_extension(f'extensions.event.{ext}')
        
        # print console feedback
            print(f'Extension {ext} was loaded successfully')
        
        # in the event of an exception
        except Exception as err:

            # print the error to console
            print(f'Extension {ext} could not be loaded {err}')
   
    # for all all the loop extensions
    for ext in loopexts:
        # try and load the extension
        try:
            client.load_extension(f'extensions.loop.{ext}')
        
        # print console feedback
            print(f'Extension {ext} was loaded successfully')
        
        # in the event of an exception
        except Exception as err:

            # print the error to console
            print(f'Extension {ext} could not be loaded {err}') 
            
    # add an endline
    print("\n")       

    # load our manually loded extensions
    client.load_extension('jishaku')
    client.load_extension('extensions.proc.presence')
