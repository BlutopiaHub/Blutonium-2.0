from client import Client
from setup import TOKEN

# Define our client variable with our subclassed discord.bot
client = Client()

# Load the initial extension
client.load_extension('extensions.proc.init')

# Run the client
client.run(TOKEN)
