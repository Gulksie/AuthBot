# set working directory to the directory the file is being run from
# this NEEDS TO BE RUN before all other import statments for saving to work properly!
import os, pathlib

os.chdir(pathlib.Path(__file__).parent.absolute())

import discord
from discord.ext import tasks
from datetime import datetime
from time import sleep as timesleep

import verify
import keepAlive

botIntents = discord.Intents(messages=True, members=True, guilds=True)
client = discord.Client(intents=botIntents)

verifiedRoles = {}

roleName = "Verified"

verifCommand = "?verif"

newUserMessage = '''You are getting this message because you joined a McMaster course server. 
Welcome! Before you can participate, we need to verify that you are a student at McMaster.
Please send an email to `macdiscords@gmail.com` with the following code in the body (subject line doesn't matter) from your McMaster email address.'''

newUserMessage2 = f'''Please note the code is only valid for {int(verify.validTime/60)} minutes, after which you'll have to request a new one by sending the `{verifCommand}` command to this dm channel.
Please do not hesitate to ask a mod or admin for help!'''

@client.event
async def on_ready():
    print(f"Logged in as {client.user} on {datetime.now()}.")


    # loop through every server we're in and do some checks
    servers = client.guilds

    for server in servers:

        # check if the required role is in the server already, and if not, make it
        verifiedRole = None

        roles = await server.fetch_roles()

        exists = False
        for role in roles:
            if role.name == roleName:
                exists = True
                verifiedRole = role
                break

        if not exists:
            print(f"Creating verified role in new server {server.name}")

            # to view permissions for this role go to https://discordapi.com/permissions.html#104189505
            # the colour is #31ffa6
            verifiedRole = await server.create_role(name=roleName, permissions=discord.Permissions(permissions=104189505), colour=discord.Colour.from_rgb(49, 255, 166))

        # check if every verified member in the server has the verified role, if not, give it to them
        memebers = await server.fetch_members().flatten()

        for member in memebers:
            if member.id in verify.verifiedUsers:
                hasRole = False

                if member.roles != [None]:  # member.roles is [None] when user has no roles
                    for role in member.roles:
                        if role.id == verifiedRole.id:
                            hasRole = True
                            break

                if not hasRole:
                    print(f"Adding new role to {member.display_name} in server {server.name}")
                    await member.add_roles(verifiedRole)

        verifiedRoles[server.id] = verifiedRole    
    print("Done setup.\n")

@client.event
async def on_member_join(member):
    print(f"New user {member.display_name} joined server {member.guild.name}")

    # check if user is verified, if they are, give them the role, if not, start the verification process
    userID = member.id
    if userID in verify.verifiedUsers:
        print(f"Adding new role to {member.display_name} in server {member.guild.name}")
        await member.add_roles(verifiedRoles[member.guild.id])
    
    else:
        await member.send(newUserMessage)
        code = verify.startVerification(userID)
        await member.send(f"`{code}`")
        await member.send(newUserMessage2)

@tasks.loop(seconds=15)
async def updateEmails():
    newUsers = verify.updateVerification()

    for user in newUsers:
        for server in client.guilds:
            member = server.get_member(user)

            if member is not None:          
                print(f"Adding new role to {member.display_name} in server {server.name}")
                await member.add_roles(verifiedRoles[server.id])

        await client.get_user(user).send("You have been verified!")

@updateEmails.before_loop
async def beforeUpdateEmails():
    await client.wait_until_ready()

# quick and dirty way to check for our verification message
@client.event
async def on_message(message):
    author = message.author
    userID = author.id

    if (message.content.startswith(verifCommand)):
        print(f"Recived verification request from {author.display_name} at {datetime.now()}")

        #check if user is already verified or in verification process, if so, quit
        if userID in verify.verifiedUsers:
            return

        for pendingCode, pendingUserID, time in verify.pendingUsers:
            if userID == pendingUserID:
                return

        await author.send(newUserMessage)
        code = verify.startVerification(userID)
        await author.send(f"`{code}`")
        await author.send(newUserMessage2)

    elif userID == 232230909363879939 and message.content == "ping":  # my personal discord id, simple command to check if bot is online
        message.channel.send(f"Pong @ {datetime.now()}")


if __name__ == "__main__":
    # below code is no longer required on non-knockoff raspbery pi server
    # timesleep(30)  # need to wait on terminal startup; networking startup takes some amount of time after the scripts are run at startup

    keepAlive.run()
    updateEmails.start()
    verify.startUp()

    # grab discord key
    with open("discordKey", "r") as f:
        authToken = f.readline().strip()

    client.run(authToken)
