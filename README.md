# PlebeianBot
Source code of the reddit bot for r/PlebeianAR

Requires praw and pyimgur...

For praw you need a praw.ini that contains  
[PlebeianBot]  
user_agent=<name it whatever>  
client_id=<bots client id>  
client_secret=<bots client secret>  
username=PlebeianBot  
password=<bots password>  
  
  
To get client_id and client_secret go to https://www.reddit.com/prefs/apps and register an app to the account  
  

For pyimgur you need a imgur_creds.json that contains  
{  
  "client_secret": "<client_secret>",  
  "refresh_token": "<refresh_token>"  
}  
