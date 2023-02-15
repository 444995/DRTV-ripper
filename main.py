from pyppeteer import launch
from lxml import html
import subprocess
import requests
import asyncio
import re
import os




# Xpath for the title of the tv show on dr.dk/drtv website
TVSHOW_TITLE_XPATH = '//*[@id="row0"]/section/div/div/div/h1'

# Xpath for the available seasons of the tv show on dr.dk/drtv website
TVSHOW_SEASONS_XPATH = '//*[@id="season-list-container"]//a'


class DRTVScraper:
    def __init__(self):
        # self.output_yt_dl
        self.temp_folder = "temp_drtv_ripper"
        self.maximum_tries = 10

        os.system('cls' if os.name == 'nt' else 'clear')
        
        tvshow_link = str(input("Enter the link to the show: "))
        tree = self.get_tree(tvshow_link)
        tvshow_title = self.fetch_tvshow_title(tree)
        self.season_dic = self.fetch_tvshow_available_seasons(tree, tvshow_link)
        season_links_to_scrape = self.get_info(tvshow_title, self.season_dic)
        
        for season_url in season_links_to_scrape:
            episode_links = asyncio.run(self.fetch_episode_links(season_url))
            self.scrape_episodes(episode_links, season_url, tvshow_title)

        print('\nScraping done!')


    def get_tree(self, url):
        response = requests.get(url)
        tree = html.fromstring(response.content)

        return tree


    def fetch_tvshow_title(self, tree):
        tvshow_title = tree.xpath(TVSHOW_TITLE_XPATH)[0].text_content()
        if not os.path.exists(tvshow_title):
            os.makedirs(tvshow_title)
        return tvshow_title


    def fetch_tvshow_available_seasons(self, tree, tvshow_link):
        try:
            tvshow_seasons = tree.xpath(TVSHOW_SEASONS_XPATH)
        except: # returns [1] if there is only one season since the xpath crashes if there is only one season
            return [1]

        # Create a dictionary to store the extracted items
        dic = {}

        # Iterate over the items and add them to the dictionary
        for item in tvshow_seasons:
            text = item.text_content().strip().replace('Sæson ', '')
            href = 'https://www.dr.dk' + item.get('href').strip()
            dic[text] = href

        # If dic is empty it returns [1] and the url since there is only one season
        if not dic:
            return {'1': tvshow_link}


        return dic


    def get_info(self, tvshow_title, season_list):
        # Extract the text values into a list and sort it
        all_available_seasons = list(season_list.keys())
        all_available_seasons.sort()
        # Splits up the list into a string separated by commas
        seasons = ", ".join(str(season) for season in all_available_seasons)

        print(f'\nTV Show name: {tvshow_title}')
        print(f'Seasons available: {seasons}')
        print('\nWhich seasons would you like to download?\n')
        seasons_to_scrape = input('> ')
        
        # splits them up and adds them to a list so if user types 1, 2, 3 or 1 and 2 and 3, it will still be ['1', '2', '3']
        seasons_to_scrape = re.findall(r'\d+', seasons_to_scrape)

        # convert strings to integers
        seasons_to_scrape = [int(num) for num in seasons_to_scrape]

        # sort the list
        seasons_to_scrape.sort()

        urls = []
        for season in seasons_to_scrape:
            if str(season) in season_list:
                urls.append(season_list[str(season)])
        return urls


    async def fetch_episode_links(self, season_url):
        episode_links = []
        
        # launch browser and create new page
        browser = await launch()
        page = await browser.newPage()
        
        # set viewport and get corresponding season number
        await page.setViewport({'width': 1, 'height': 1})
        specific_season = self.get_corresponding_season(season_url)
        
        # navigate to season URL
        print(f'\nScraping episode links from season {specific_season} | url: {season_url}\n')
        await page.goto(season_url)
        await asyncio.sleep(2)  # wait for 2 seconds to make the page load
        
        # Click the "show more" button, if present
        button_selector = '#row1 > section > div:nth-child(2) > div.show-more-episodes__show-more-button__wrapper > button'
        try:
            await page.click(button_selector)
        except:
            pass

        # Loop through each episode element and extract link
        episode_count = 0
        while True:
            try:
                episode_count += 1
                episode_element = await page.xpath(f'/html/body/div[2]/div/div[1]/div[1]/main/div[2]/div/section[2]/section/div[2]/div/div[{episode_count}]/div/a')
                episode_link = await (await episode_element[0].getProperty('href')).jsonValue()
                episode_link = episode_link.replace('https://www.dr.dk/drtv/episode/', 'https://www.dr.dk/drtv/se/')
                episode_links.append(episode_link)
                
                # Click the "show more" button, if present again
                try:
                    await page.click(button_selector)
                except:
                    pass
            except:
                break
        
        # close browser and return episode links
        await browser.close()
        return episode_links


    def scrape_episodes(self, episode_links, season_url, tvshow_title):
        # Get the season number
        specific_season = int(self.get_corresponding_season(season_url))
        
        # Loop through all the episode links
        for count, url in enumerate(episode_links, start=1):
            # Format season and episode numbers as zero-padded strings if less than 10
            season_str = f'S{specific_season:02d}'
            episode_str = f'E{count:02d}'
            print(f'Downloading {season_str}{episode_str} | url: {url}')
            
            tries = 0
            while tries < self.maximum_tries:
                try:
                    tries += 1
    
                    # Download the video using youtube-dl
                    output = subprocess.check_output(['youtube-dl', '--no-call-home', '-o', f'{tvshow_title}/%(title)s.%(ext)s', '--verbose', url], stderr=subprocess.STDOUT)
                    filename = output.decode('iso-8859-1').strip()  # Get last line of output

                    # Get the current filename of the media file from the output
                    match = re.search(r'\[ffmpeg\] Merging formats into "(.*?)"', filename)
                    if match: 
                        filename = match.group(1)
                    else: 
                        print(f'Error downloading {season_str}{episode_str} | url: {url}')
                                        
                    # Get the new filename with the right format
                    file_ext = os.path.splitext(filename)[1]
                    new_filename = f'{tvshow_title}.{season_str}{episode_str}{file_ext}'
                    
                    # Move the downloaded file to the right directory with the right filename
                    os.makedirs(os.path.join(tvshow_title, f'Season {specific_season}'), exist_ok=True)

                    # Use zero-padded strings for season and episode numbers if less than 10 to get for example S01E01 instead of S1E1
                    if specific_season < 10:
                        new_filename = f'{tvshow_title}.{season_str}{episode_str}'
                    else:
                        new_filename = f'{tvshow_title}.{season_str}{episode_str}'

                    # Rename the file
                    os.rename(filename, f'{tvshow_title}\\Season {specific_season}\\' + new_filename + file_ext)
                    
                    # Break out of the retry loop if the download was successful
                    break

                except:
                    # Retry if there was an error, unless the maximum number of tries has been reached
                    if tries == self.maximum_tries:
                        print(f'Error downloading {season_str}{episode_str} | url: {url}')
                    else:
                        print(f'Retrying {season_str}{episode_str} ({tries}/{self.maximum_tries}) | url: {url}')


    def get_corresponding_season(self, url):
        """
        Returns the specific season that corresponds to the url
        """
        for season, link in self.season_dic.items():
            if link == url:
                return season


if __name__ == "__main__":
    DRTVScraper()
