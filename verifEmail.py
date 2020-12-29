import smtplib
import imaplib
import email
import atexit
from datetime import datetime

# with open("loginDetails", "r") as f:
#     loginDetails = f.readlines()

# usr, psswd = loginDetails[0].split(',')

# # redundant but ig we can keep these around in case we ever move to custom servers (not happening but ok)
# sendPort = 465  # defualt port for smtp with ssl
# recivePort = 935  # same as above for imap

# reciveServer = imaplib.IMAP4_SSL("imap.gmail.com")

# print("Logging in to email")
# reciveServer.login(usr, psswd)
# print(f"Logged in to email at {datetime.now()}")
# reciveServer.select()  # goes to defualt mailbox, the inbox

reciveServer = None
def login():
    global reciveServer
    reciveServer = imaplib.IMAP4_SSL("imap.gmail.com")

    print("Logging into email")
    with open("/home/gulk/authbot/loginDetails", "r") as f:
        loginDetails = f.readlines()

    usr, psswd = loginDetails[0].split(',')

    reciveServer.login(usr, psswd)
    print(f"Logged in to email at {datetime.now()}")
    reciveServer.select()  # goes to defualt mailbox, the inbox

def getNewValidEmails():
    reciveServer.noop()  # noop can basically poll for new emails (it really does nothing but dont worry about it)
    
    emailIDs = reciveServer.search(None, "UnSeen")[1][0]  # when we read new emails they're marked as seen so we dont need to care about them in the future
    emailIDs = emailIDs.split()
    if len(emailIDs) < 1:
        return []

    validEmails = []

    for i in emailIDs:
        mail = reciveServer.fetch(i, "(RFC822)")  # FRC822 is a standard for reading emails
        msgData = mail[1][0][1]  # this object contains a lot of data that was pretty much useless to me, so we gotta ignore it
        
        if type(msgData) is int:  # this happens after the first email for some reason
            msgData = mail[1][1][1]

        msg = email.message_from_bytes(msgData)

        print(f"Recived new email from {msg['from']}")
        
        # grab message author
        # authors are returned as First Last <email@address.com>, meaning we need to do a bit of parsing to get the actual email
        author = msg["from"].lower().split()
        author = author[len(author)-1]
        author = author[1:-1]

        user, server = author.split("@")

        print(author)

        # if the email is from the mcmaster domain, we assume its valid, 
        if server == "mcmaster.ca":
            print("Address is a valid mac address")
            content = recursiveMultipart(msg)
            # if msg.is_multipart():
            #     content = []
            #     for message in msg.get_payload():
            #         content.append(message.get_payload())

            # else:
            #     content = [msg.get_payload()]

            validEmails.append([user, content])
    
    return validEmails  # format [[macID, [content]], ...]

def recursiveMultipart(msg):
    content = []
    if msg.is_multipart():
        for message in msg.get_payload():
            content.append(recursiveMultipart(message))

    else:
        content = [msg.get_payload()]

    return flatten(content)  # flattens list

# https://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists
def flatten(A):
    rt = []
    for i in A:
        if isinstance(i,list): rt.extend(flatten(i))
        else: rt.append(i)
    return rt

def cleanUp():
    print(f"Logging out of email at {datetime.now()}")
    reciveServer.logout()

atexit.register(cleanUp)

if __name__ == "__main__":
    login()
    emails = getNewValidEmails()
    print(emails)
