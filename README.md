- Does not work properly at the moment - I'm working on a new one.
# DRTV-ripper - dr.dk/drtv
DRTV-ripper is a software tool that is able to help rip specific shows or movies from dr.dk/drtv. It is built using modules such as pyppeteer, asyncio, and youtube-dl - and can be used via a simple and easy to understand console interface.

Please note that, at present, the download speed may be slower than expected. This is because yt-dlp is not currently compatible with DRTV shows and movies, and youtube-dl is being used as an alternative. However, despite its reduced speed, the software remains highly functional and can still be used to download the desired content.

# Why use this over yt-dlp or youtube-dl?
You might think to yourself why you should pick this over yt-dlp or youtube-dl, the answer is simple: this software offers an easy-to-use console interface that allows even the newest users to rip specific shows or movies from DRTV. Additionally, with DRTV-ripper it automatically categorizes and names downloaded media correctly, which can save you time and effort. While yt-dlp and youtube-dl are decent options, they often do not properly rename downloaded media, and can be difficult for new users to navigate.
Also, it's not always that youtube-dl or yt-dlp works properly - in my experience at least.

# Functions in the near future
These are some of the functions I plan to add to the code:

* Year added to episode title by scraping the year from dr.tv
* Timedate to console output
* Option to pick own quality
* Add download progress when downloading (if possible)
* Auto subtitles (wouldn't work for a lot of media tho since a lot of it is not very known, so no subtitles would be available)
* Auto sync subtitles (pretty easy)

# Errors to fix
These are the errors that are gonna get fixed:
* Sort by episode date instead - right now some shows are apparently sorted in reverse order on the website (they are so braindead)
* Create the season folders at the "fetch_tvshow_available_seasons" function instead
* All downloaded media gets empty subtitles - can probably be removed with ffmpeg

# Installation
1. Git clone this repo by doing 'git clone ...' or download the repo zip file
2. Do 'pip install -r requirements.txt' 
3. Install ffmpeg (important!)
4. Run main.py
