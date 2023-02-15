# DRTV-ripper
DRTV-ripper is a software tool that facilitates the ripping of specific shows. It is built using modules such as pyppeteer, asyncio, and youtube-dl - and can be used via a simple and easy to understand console interface.

Please note that, at present, the download speed may be slower than expected. This is because yt-dlp is not currently compatible with DRTV shows, and youtube-dl is being used as an alternative. However, despite its reduced speed, the software remains highly functional and can still be used to download the desired content.

Although the code is currently a mess, I plan to clean it up in the near future.

And I will be sure to implement ripping movies an option as quickly as possible also! Even though it's pretty easy to do yourself with youtube-dl - but shhhh...

# Functions in the near future
These are some of the functions I plan to add to the code:

* Sort by episode date instead - right now some shows are apparently sorted in reverse order on the website (they are so braindead)
* Year added to episode title by scraping the year from dr.tv
* Timedate to console output
* Remove temp_drtv_ripper folder because it's technically not needed
* Option to pick own quality
* Option to download all seasons by typing 'all'

# Installation
1. Git clone this repo by doing 'git clone ...'
2. Do 'pip install -r requirements.txt' 
3. Install ffmpeg (important!   )
4. Run main.py


