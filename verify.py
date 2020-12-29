from datetime import datetime
import yaml
import secrets

import verifEmail

# set of userIDs of all verified users
verifiedUsers = {232230909363879939}

# pending users are in format [[code, userID, time created], ...]
pendingUsers = []
pendingKeys = []

# the time each code is valid for, in seconds
validTime = 5 * 60

fileName = "/home/gulk/authbot/users.yaml"

def startUp():
    verifEmail.login()
    verifiedUsers.update(loadVerifiedUsers())

def loadVerifiedUsers(justIDs=True):
    # justIDs specifies if the load should include only the discord IDs

    with open(fileName, "r+") as f:
        users = yaml.safe_load(f)

    if justIDs:
        return set() if users is None else set(users.keys())
    else:
        return dict() if users is None else users

def saveVerifiedUsers(ids, macIDs):
    users = loadVerifiedUsers(False)
    
    # create a dict associating each userID with their macID
    newUsers = {}
    for i in range(len(ids)):
        newUsers[ids[i]] = macIDs[i]

    # add this new dict to the existing dict, and write it to the file
    users.update(newUsers)

    with open(fileName, "w") as f:
        yaml.safe_dump(users, f)

def startVerification(userID):
    print("Starting verification process...")
    while 1:
            secretCode = secrets.token_urlsafe(32)
            if secretCode not in pendingKeys:
                break
    
    pendingKeys.append(secretCode)
    pendingUsers.append([secretCode, userID, datetime.now()])

    return secretCode

def updateVerification():
    print(f"Checking verification (emails) at {datetime.now()}")
    emails = verifEmail.getNewValidEmails()

    if emails is None or emails == []:
        print("no valid emails")
        return []
    
    newVerified = []
    macIDs = []
    # loop through all pending users, and check if the secret code for that user is present in any email. If it is, mark that user as verified and remove their pending thingy
    for i in range(len(pendingUsers)):
        secretKey, userID, timeCreated = pendingUsers[i]

        if (datetime.now() - timeCreated).seconds > validTime:  # key is no longer valid, delete it
            print(f"Deleting invalid key for user id: {userID}")
            pendingUsers.pop(i)
            continue

        # loop through emails, check their content(s), and if the key is inside those contents
        for email in emails:
            contents = email[1]
            
            matchesSecret = False
            for content in contents:
                if secretKey in content:
                    matchesSecret = True
                    break

            if matchesSecret:
                print(f"User id {userID} is now verified")
                verifiedUsers.add(userID)
                pendingUsers.pop(i)
                macIDs.append(email[0])
                emails.remove(email)
                newVerified.append(userID)
                break
    
    saveVerifiedUsers(newVerified, macIDs)

    return newVerified
