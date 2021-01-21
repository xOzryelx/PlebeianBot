# PlebeianBot
Source code of the reddit bot for r/PlebeianAR

Requires praw and pyimgur...
For praw you need a praw.ini next to these scripts that contains  
[PlebeianBot]  
user_agent=  
client_id=  
client_secret=  
username=  
password=  

For pyimgur you need a auth key linked to my account or change the imgur_client = pyimgur.Imgur line in PlebBot_ImgurRepost.py  
Changed line 1090 in pyimgur \_\_init\_\_.py from http to https and line 1143 from /3/image to /3/upload

I'll make a pull for that eventually
