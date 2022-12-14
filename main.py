import configparser
import datetime
from os import stat
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import asyncpraw as praw
from random import randint
from asyncpraw.models import MoreComments
import sqlite3 as sl

#Create the SQLite Database to store user activity info (and other info)
con = sl.connect('info.db')

#Credentials ini file initilization
config = configparser.ConfigParser()
config.read('credentials.ini')

#Stats ini file initilization
stats = configparser.ConfigParser()
stats.read('stats.ini')

#Other config ini file initilization
other = configparser.ConfigParser()
other.read('other.ini')

#bcolors for print
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
erasureCalled = False

print(f"{bcolors.OKGREEN}Initilizing {bcolors.OKCYAN}{bcolors.BOLD}The Wandering Cosmos {bcolors.ENDC}{bcolors.OKGREEN}bot...{bcolors.ENDC}")

#The glorious list where people are pulled from
subs = other['CONFIG']['subs'].splitlines()

print(f"{bcolors.OKGREEN}Pulling users from these subreddits {bcolors.OKCYAN}{subs}{bcolors.ENDC}")

#The Wandering Cosmos Subreddit. Makes writing code quicker
subN = "TheWanderingCosmos"

#RNG Stuff
luckynumber = int(other['CONFIG']['luckynumber'])
postrng = int(other['CONFIG']['postrng'])
commentrng = int(other['CONFIG']['commentrng'])

#Soft Limits (Corresponding value may be higher or lower by a bit)
usLimit = 1000

#Hard Limits (Corresponding value will be exact)
pullLimit = int(other['CONFIG']['pullLimit'])
pullComments = int(other['CONFIG']['pullComments'])
pullScore = int(other['CONFIG']['pullScore'])

#Initilize the reddit instance and save it for later. (Uses the login info from the credentials.ini)
def redditConnect():
    reddit = praw.Reddit(
        client_id=config['SETTINGS']['client_id'],
        client_secret=config['SETTINGS']['client_secret'],
        user_agent="The Wandering Cosmos Bot",
        username=config['SETTINGS']['username'],
        password=config['SETTINGS']['password'],
    )
    return reddit

async def updateFlair(reddit, unum):
    #SQL selects the user and stores the user's name and number
    sql = """SELECT * FROM USER where number='{}'""".format(unum)
    cursor = con.cursor()
    Data = cursor.execute(sql).fetchone()
    uNumber = int(Data[0])
    uName = str(Data[1])
    cursor.close()

    #Check if the user is on the ignore list
    check = any(i in uName for i in stats['IGNORE']['userlist'].splitlines())
    #If they aren't, continue
    if check == False:
        #Assign the flair based on their number
        if uNumber <= 25:
            subAwait = await reddit.subreddit(subN)
            await subAwait.flair.set(uName, text="Cosmos Drifter"+" #"+str(uNumber))
            await reddit.close()
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{uName} {bcolors.OKGREEN}was given the flair {bcolors.OKCYAN}Cosmos Drifter #{uNumber}{bcolors.ENDC}")
        elif 25 < uNumber <= 125:
            subAwait = await reddit.subreddit(subN)
            await subAwait.flair.set(uName, text="Sentinel"+" #"+str(uNumber-25))
            await reddit.close()
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{uName} {bcolors.OKGREEN}was given the flair {bcolors.OKCYAN}Sentinel #{uNumber}{bcolors.ENDC}")
        elif 125 < uNumber <= 375:
            subAwait = await reddit.subreddit(subN)
            await subAwait.flair.set(uName, text="Nomad"+" #"+str(uNumber-125))
            await reddit.close()
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{uName} {bcolors.OKGREEN}was given the flair {bcolors.OKCYAN}Nomad #{uNumber}{bcolors.ENDC}")
        elif 375 < uNumber <= 875:
            subAwait = await reddit.subreddit(subN)
            await subAwait.flair.set(uName, text="Keeper"+" #"+str(uNumber-375))
            await reddit.close()
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{uName} {bcolors.OKGREEN}was given the flair {bcolors.OKCYAN}Keeper #{uNumber}{bcolors.ENDC}")
        elif uNumber > 875:
            subAwait = await reddit.subreddit(subN)
            await subAwait.flair.set(uName, text="Wanderer"+" #"+str(uNumber-875))
            await reddit.close()
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{uName} {bcolors.OKGREEN}was given the flair {bcolors.OKCYAN}Wanderer #{uNumber}{bcolors.ENDC}")
        else:
            subAwait = await reddit.subreddit(subN)
            await subAwait.flair.set(uName, text="Bot Brokey?"+" #"+str(uNumber))
            await reddit.close()
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{uName} {bcolors.OKGREEN}was given the flair {bcolors.OKCYAN}Bot Brokey? #{uNumber}{bcolors.ENDC}")
    else:
        #If they are on the ignore list, ignore them and print the outcome
        print(f"{bcolors.WARNING}- User {bcolors.OKCYAN}{uName} {bcolors.WARNING}was not given a flair as they are on the ignore list{bcolors.ENDC}")

# Adds the user to the sub
async def inviteUser(reddit, user):
    #sql to check if user is already invited
    checksql = """SELECT name FROM USER where name='{}'""".format(user)
    cursor = con.cursor()
    Data = cursor.execute(checksql).fetchone()
    cursor.close()
    #If the user is not in the database, invite them. Otherwise print out that they were not invited.
    if str(Data) == "None":
        #Get the users number and update the ini file
        num = int(stats['STATS']['Users']) + 1
        stats.set('STATS', 'Users', str(num))
        with open('stats.ini', 'w') as configfile:
            stats.write(configfile)

        #Print that the user was invited
        print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{user} {bcolors.OKGREEN}was invited successfully. There are now {bcolors.OKCYAN}{str(num)} {bcolors.OKGREEN}users.{bcolors.ENDC}")

        #Add the user as a contributor
        subAwait = await reddit.subreddit(subN)
        await subAwait.contributor.add(user)
        #Gives them the flair for new joins
        check = any(i in str(user) for i in stats['IGNORE']['userlist'].splitlines())
        if check == False:
            subAwait = await reddit.subreddit(subN)
            await subAwait.flair.set(user, text="Stray")
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{user} {bcolors.OKGREEN}was given the flair {bcolors.OKCYAN}Stray{bcolors.ENDC}")
        else:
            print(f"{bcolors.WARNING}- User {bcolors.OKCYAN}{user} {bcolors.WARNING}was not given a flair as they are on the ignore list{bcolors.ENDC}")

        #Add the user to the SQLite DB
        sql = """INSERT INTO USER
            (number, name, active)
            VALUES ('{}','{}','{}');""".format(num, user, True)

        cursor = con.cursor()
        cursor.execute(sql)
        con.commit()
        cursor.close()
    else:
        print(f"{bcolors.WARNING}- User {bcolors.OKCYAN}{user} {bcolors.WARNING}has not been invited. REASON: {bcolors.OKCYAN}{user} {bcolors.WARNING}is already a member{bcolors.ENDC}")
    return

async def updateSQL():
    lastNum = 0
    for i in range(1, int(stats['STATS']['users'])):
        #Get the user with the number i
        sqlC = """SELECT * FROM USER where number='{}'""".format(i)
        cursor = con.cursor()
        Data = cursor.execute(sqlC).fetchone()
        #print(Data)
        cursor.close()
        #If they exist, set their number
        if str(Data[1]) != "None":
            if i == 1:
                lastNum = 1
            if i == int(Data[0]):
                lastNum = int(Data[0])
            else:
                updateSQL = """UPDATE USER SET number='{}' where name='{}'""".format(lastNum+1,str(Data[1]))
                cursor = con.cursor()
                cursor.execute(updateSQL)
                con.commit()
                cursor.close()
                lastNum = lastNum+1
    #Update the SQLite database with the new number information

            #Update the flair's of everyone who has a number lower than the user
            await updateFlair((redditConnect()), 1)
    return

# Removes the user from the sub
async def removeUser(reddit, user):
    #Remove a a number from the counter and update the ini
    num = int(stats['STATS']['Users']) - 1
    stats.set('STATS', 'Users', str(num))
    with open('stats.ini', 'w') as configfile:
        stats.write(configfile)

    #Print that the user was removed
    print(f"{bcolors.WARNING}- User {bcolors.OKCYAN}{user} {bcolors.WARNING}is being removed. There will be {bcolors.OKCYAN}{str(num)} {bcolors.WARNING}users.{bcolors.ENDC}")

    #Removes the user as a contributor from the sub
    try:
        subAwait = await reddit.subreddit(subN)
        await subAwait.contributor.remove(user)
        await reddit.close()
    except:
        print(f"Error removing {user}, their account may no longer exist")
        await reddit.close()


    #Get the user's number
    sqlA = """SELECT number FROM USER where name='{}'""".format(user)
    cursor = con.cursor()
    Data = cursor.execute(sqlA).fetchone()
    uNumber = int(Data[0])
    cursor.close()

    #Remove the user from the SQLite DB
    sqlB = """DELETE FROM USER where name='{}'""".format(user)
    cursor = con.cursor()
    cursor.execute(sqlB)
    con.commit()
    cursor.close()

    
    return

#Finds users and runs rng on them to see if they should be invited
async def findUser(reddit):
    #Increment through the subreddit list
    for i in subs:
        subreddit = i
        #Look for the top new submissions
        subAwait = await reddit.subreddit(subreddit)
        async for submission in subAwait.new(limit=pullLimit):
            #Check if they are upvoted by a certain amount
            if(submission.score > pullScore):
                #If they are, check for best comments
                submission.comment_sort = "best"
                submission.comment_limit = pullComments
                #Make sure they are not "MoreComments" comments
                commentAwait = await submission.comments()
                for comment in commentAwait:
                        if isinstance(comment, MoreComments):
                            continue
                        #If it is not, rng check for if they should be invited
                        if(randint(1,commentrng) == luckynumber):
                            author = comment.author
                            await inviteUser(redditConnect(), str(author))
                #rng check if they should be invited
                if(randint(1,postrng) == luckynumber):
                    author = submission.author
                    await inviteUser(redditConnect(), str(author))
    print(f"{bcolors.OKCYAN}- Done pulling users{bcolors.ENDC}")
    await reddit.close()

#Checks if given user has been active within the week returns true or false based on activity
async def checkIfUserActive(reddit, user):
    i = 0
    x = 0
    time = datetime.datetime.now().timestamp()
    #Set the sub to TheWanderingCosmos
    subreddit = await reddit.subreddit(subN)
    #Search the sub for posts from the user within the last week
    try:
        async for post in subreddit.search(f'author:"{user}"',time_filter='week'):
            #If found count the posts
            i = i+1
            break
    except:
        print("Error")
        #There may have been an error finding the user, their posts, or comments. Assume they were inactive. Closes the reddit session and returns False
        await reddit.close()
        return False
    #Check the amount of posts
    if i <= 0:
        #If there are none, check for comments
        redditor = await reddit.redditor(user)
        try:
            #Fetch the comments from the user
            async for comment in redditor.comments.new(limit=300):
                #Check the subreddit they were from
                if comment.subreddit == subN:
                    #If they are from the currect sub, check the time they were posted and compare it to the current time
                    dif = (float(time)-float(comment.created_utc))/(60*60*24)
                    #If the time posted is within the week, count the comment
                    if dif < 9:
                        x = x+1
                        break
                #await asyncio.sleep(.05)
            #Check the comment amount
            if x <= 0:
                #If 0, the user is inactive. Closes the reddit session and returns False
                await reddit.close()
                return False
            else:
                #If there are more than 0, the user is active. Closes the reddit session and returns True
                await reddit.close()
                return True
        except:
            print("Error")
            #There may have been an error finding the user, their posts, or comments. Assume they were inactive. Closes the reddit session and returns False
            await reddit.close()
            return False
    else:
        #If they have posted on the sub, they were active. Closes the reddit session and returns True
        await reddit.close()
        return True

#The Great Erasure removes everyone who was not active in the last week
async def greatErasure(reddit):
    #Variables
    inactive = []
    #Get all users
    sql = """SELECT * FROM USER"""
    cursor = con.cursor()
    Data = cursor.execute(sql).fetchall()
    cursor.close()
    #Check for activity
    for i in Data:
        if await checkIfUserActive(redditConnect(), i[1]) != True:
            #Add the user to the inactive list
            inactive.append(i[1])
            print(f"{bcolors.WARNING}User {bcolors.OKCYAN}{i[1]} {bcolors.WARNING}was inactive.{bcolors.ENDC}")
        else:
            print(f"{bcolors.OKGREEN}User {bcolors.OKCYAN}{i[1]} {bcolors.OKGREEN}was active.{bcolors.ENDC}")
    formatlist = ""
    #Remove all users on the inactive list
    for x in inactive:
        #Temporary variables
        fName = ""
        #Get the user's number for formatting
        sql = """SELECT * FROM USER where name='{}'""".format(x)
        cursor = con.cursor()
        Data = cursor.execute(sql).fetchone()
        iNum = int(Data[0])
        #Get the user's flair
        if iNum <= 25:
            fName = "Cosmos Drifter #"+str(iNum)
        elif 25 < iNum <= 125:
            fName = "Sentinel #"+str(iNum-25)
        elif 125 < iNum <= 375:
            fName = "Nomad #"+str(iNum-125)
        elif 375 < iNum <= 875:
            fName = "Keeper #"+str(iNum-375)
        elif iNum > 875:
            fName = "Wanderer #"+str(iNum-875)
        cursor.close()
        #Format the list into a bullet list
        
        formatlist = formatlist+"\n* "+fName+" - u/"+x
        check = any(i in x for i in stats['IGNORE']['userlist'].splitlines())

        if check == False:
            await removeUser(redditConnect(), x)
            print(f"{bcolors.WARNING}- User {bcolors.OKCYAN}{x} {bcolors.WARNING}was removed for inactivity.{bcolors.ENDC}")
        else:
            print(f"{bcolors.OKGREEN}- User {bcolors.OKCYAN}{x} {bcolors.OKGREEN}was not removed for inactivity as they are on the ignore list{bcolors.ENDC}")

    #The Great Erasure Post (Post all the users erased)
    #Get the current date and time
    ufDate = datetime.datetime.today()
    #Format it to just the date in DD-MM-YYYY format and make sure it is a string
    fDate = str(ufDate.strftime("%d-%m-%Y"))
    #Flair ID for meta posts
    flair = "a702bea4-4b6d-11ed-8d3d-aef57245af7f"
    #Post title
    title = "The Great Erasure ["+fDate+"]"

    total = stats['STATS']['users']

    #Create the body text
    body = f"**The following user(s) have been removed for inactivity**: \n\n {formatlist} \n\nThere are now {total} approved users remaining."
    #Submit the post to the subreddit
    subAwait = await reddit.subreddit(subN)
    await subAwait.submit(title, selftext=body, flair_id=flair)
    await reddit.close()
    return

async def asyncUserInvite(wait):
    await asyncio.sleep(wait)
    if int(stats['STATS']['users']) < usLimit:
        print(f"{bcolors.WARNING}Under {bcolors.OKCYAN}{usLimit} {bcolors.WARNING}users. Looking for more users.{bcolors.ENDC}")
        await findUser(redditConnect())
    elif int(stats['STATS']['users']) >= usLimit:
        print(f"{bcolors.OKGREEN}There are {bcolors.OKCYAN}{str(stats['STATS']['users'])} {bcolors.OKGREEN}users. Not adding more users.{bcolors.ENDC}")
    

async def asyncCheckDateTime():
    unformatted = datetime.datetime.now()
    cdtime = [str(unformatted.strftime("%A")), str(unformatted.strftime("%H"))]
    return cdtime


#Main loop
async def MainLoop():
    erasureCalled = False
    #Define the current time and day, then print the time and day the function was called
    dtLog = datetime.datetime.now()
    print(f"{bcolors.OKBLUE}- Main function called at {bcolors.OKCYAN}{str(dtLog)}{bcolors.ENDC}")
    #Get the day and the hour
    dayhour = await asyncCheckDateTime()
    day = dayhour[0]
    hour = dayhour[1]
    #Check if the day is Sunday or Monday
    if day == "Tuesday":
        #If Sunday, check the time
        if hour == "03":
            #Make sure the great erasure is called only once
            if erasureCalled == False:
                erasureCalled = True
                #If it is 11PM, start The Great Erasure and then invite users
                print(f"{bcolors.WARNING}The Great Erasure has started!{bcolors.ENDC}")
                await greatErasure(redditConnect())
                print(f"{bcolors.OKGREEN}Inviting new users after The Great Erasure{bcolors.ENDC}")
                await asyncUserInvite(1)
            else:
                print(f"{bcolors.OKGREEN}The Great Erasure has past. Inviting new users{bcolors.ENDC}")
                await asyncUserInvite(1)
    elif day == "Sunday":
        if hour == "00":
            erasureCalled = False
        #If the day is Monday, invite users
        print(f"{bcolors.OKGREEN}It's Monday! Inviting users!{bcolors.ENDC}")
        await asyncUserInvite(1)
    elif day == "Tuesday":
        #If the day is Tuesday, invite users
        print(f"{bcolors.OKGREEN}It's Tuesday! Inviting users!{bcolors.ENDC}")
        await asyncUserInvite(1)
    return


#Debug and test code

#inviteUser(redditConnect(), "ImCarsenDev")
#inviteUser(redditConnect(), "__Havoc__")

#removeUser(redditConnect(), "ImCarsenDev")

#print(checkIfUserActive(redditConnect(), "__Havoc__"))

#updateFlair(redditConnect(), 1)

#greatErasure(redditConnect())

#findUser(redditConnect())

#Release/Run Code

#async def Test():
#    for i in range(1,564):
#        await updateFlair(redditConnect(), i)
#    return

asyncio.run(greatErasure(redditConnect()))

#if __name__ == '__main__':
#    scheduler = AsyncIOScheduler()
#    scheduler.add_job(MainLoop, 'interval', seconds=900)
#    scheduler.start()

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
#    try:
#        asyncio.get_event_loop().run_forever()
#    except (KeyboardInterrupt, SystemExit):
#        pass