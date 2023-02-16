from pyppeteer import launch
from lxml import html
import subprocess
import requests
import asyncio
import re
import os


# XPath for the title of the tv show on dr.dk/drtv website
TITLE_XPATH = '//*[@id="row0"]/section/div/div/div/h1'

# XPath for the available seasons of the tv show on dr.dk/drtv website
TVSHOW_SEASONS_XPATH = '//*[@id="season-list-container"]//a'


class DRTVScraper:
    def __init__(self):
        # self.output_yt_dl
        self.maximum_tries = 10

        os.system('cls' if os.name == 'nt' else 'clear')
        
        print('Pick an option\n1. TV show\n2. Movie\n')
        option = int(input('> '))

        if option == 1:
            print('')
            tvshow_link = str(input("Enter the link to the TV show: "))
            self.convert_media = str(input("Convert media from .mp4 to .mkv? It's lossless - (y/n): "))
    
            tree = self.get_tree(tvshow_link)
            tvshow_title = self.fetch_title(tree)
            self.season_dic = self.fetch_tvshow_available_seasons(tree, tvshow_link)
            season_links_to_scrape = self.get_info(tvshow_title, self.season_dic)

            for season_url in season_links_to_scrape:
                episode_links = asyncio.run(self.fetch_episode_links(season_url))
                self.scrape_episodes(episode_links, season_url, tvshow_title)
                
        elif option == 2:
            print('')
            movie_link = str(input('Enter the link to the movie: '))
            self.convert_media = str(input("Convert media from .mp4 to .mkv? It's lossless - (y/n): "))
            tree = self.get_tree(movie_link)
            movie_title = self.fetch_title(tree)
            self.scrape_movie(movie_title, movie_link)

        else:
            print('Seems like you entered an invalid option.')
            exit()

        print('\nProcess is finished!')
        input('')


    def get_tree(self, url):
        # Get the html tree from the url
        response = requests.get(url)

        # Parse the html tree
        tree = html.fromstring(response.content)
        return tree


    def fetch_title(self, tree):
        # Extract the title of the tv show
        title = tree.xpath(TITLE_XPATH)[0].text_content()


        # Replace all illegal characters
        title = re.sub(r'[\\/:*?"<>|]' , ' -', title)

        # Create a folder with the title of the tv show
        os.makedirs(title, exist_ok=True)

        return title


    def fetch_tvshow_available_seasons(self, tree, tvshow_link):
        # Tries to get the seasons from the xpath
        try: 
            tvshow_seasons = tree.xpath(TVSHOW_SEASONS_XPATH)
        except: 
            # returns [1] if there is only one season since the xpath crashes if there is only one season
            return {'1': tvshow_link}

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
        
        # Extracts all the valid numbers from the input
        seasons_to_scrape = re.findall(r'\d+', seasons_to_scrape)

        # Convert strings to integers
        seasons_to_scrape = [int(num) for num in seasons_to_scrape]

        # Check if seasons_to_scrape input is valid and if not, exit
        for season in seasons_to_scrape:
            if str(season) not in season_list:
                print(f'\nSeason {season} is not available. Please try again.')
                exit()

        # Sort the list
        seasons_to_scrape.sort()

        # Create a list to store the urls
        urls = []
        for season in seasons_to_scrape:
            if str(season) in season_list:
                urls.append(season_list[str(season)])

        return urls


    async def fetch_episode_links(self, season_url):

        # Launch browser and create new page
        browser = await launch()
        page = await browser.newPage()
        
        # Set viewport and get corresponding season number
        await page.setViewport({'width': 1, 'height': 1})

        # Get the corresponding season number from the url using the dic
        specific_season = self.get_corresponding_season(season_url)
        
        # navigate to season URL
        print(f'\nScraping episode links from season {specific_season} | url: {season_url}\n')
        await page.goto(season_url)
        await asyncio.sleep(2)  # wait for 2 seconds to make the page load

        # Get the button selector for the show more button to load more episodes
        button_selector = '#row1 > section > div:nth-child(2) > div.show-more-episodes__show-more-button__wrapper > button'

        # Evaluate the button element and click it if it exists
        try:
            await page.evaluate(f'document.querySelector("{button_selector}").click()')
        except:
            pass

        # Loop through each episode element and extract link
        episode_count = 0

        # Create a list to store the episode links
        episode_links = []
        while True:
            try:
                # Get the episode link and append it to the list
                episode_count += 1
                
                episode_element = await page.xpath(f'//*[@id="row1"]/section/div[2]/div/div[{episode_count}]/div/a')
                episode_link = await (await episode_element[0].getProperty('href')).jsonValue()

                # Replaces episode with se to get the correct link
                episode_link = episode_link.replace('/episode/', '/se/')

                # Append the link to the list
                episode_links.append(episode_link)
                
                # Click the "show more" button, if present again
                try:
                    await page.evaluate(f'document.querySelector("{button_selector}").click()')
                except:
                    pass

            except: # If there are no more episodes, it will break the loop
                break
        
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

            # Print the episode number and url
            print(f'Downloading {season_str}{episode_str} | url: {url}')
            
            tries = 0
            while tries < self.maximum_tries:
                try:
                    # Download the video using youtube-dl
                    output = subprocess.check_output(
                        [
                            'youtube-dl', '--no-call-home', '-o',
                            f'{tvshow_title}/%(title)s.%(ext)s', '--verbose', url
                        ], stderr=subprocess.STDOUT)

                    # Decode the output and send it to the get_filename function
                    console_output = output.decode('iso-8859-1').strip()
                    filename = self.get_filename(console_output, tvshow_title, url)
                    
                    # Get the new filename with the right format
                    file_ext = os.path.splitext(filename)[1]

                    # Create the season directory if it doesn't exist
                    os.makedirs(os.path.join(tvshow_title, f'Season {specific_season}'), exist_ok=True)

                    # Convert the file to mkv if the user wants to and the file is an mp4
                    if self.convert_media.lower() == 'y' and file_ext == '.mp4':
                        output_filename = os.path.splitext(filename)[0] + '.mkv'
                        subprocess.check_output(['ffmpeg', '-i', filename, '-c', 'copy', output_filename], stderr=subprocess.STDOUT)
                        os.remove(filename)
                        filename = output_filename

                    # Rename the file and move it to the right directory
                    new_file_ext = os.path.splitext(filename)[1]

                    # New filename with the right format
                    new_filename = f'{tvshow_title}.{season_str}{episode_str}{new_file_ext}'

                    # Create the new path and rename the file to the new path
                    new_path = f'{tvshow_title}/Season {specific_season}/{new_filename}'
                    os.rename(filename, new_path)
                    
                    # Break out of the retry loop if the download was successful                                                        
                    break

                except:
                    # Retry if there was an error, unless the maximum number of tries has been reached
                    if tries == self.maximum_tries:
                        print(f'Error downloading {season_str}{episode_str} | url: {url}')
                    else:
                        tries += 1
                        print(f'Retrying {season_str}{episode_str} - {tries}/{self.maximum_tries} tries | url: {url}')


    def scrape_movie(self, movie_title, movie_link):
        # Create the movie directory if it doesn't exist
        os.makedirs(movie_title, exist_ok=True)

        # Download the movie using youtube-dl
        print(f'\nDownloading {movie_title} | url: {movie_link}')
        output = subprocess.check_output(['youtube-dl', '--no-call-home', '-o', f'{movie_title}/%(title)s.%(ext)s', '--verbose', movie_link], stderr=subprocess.STDOUT)
       
        # Get the filename of the downloaded file
        filename = self.get_filename(output, movie_title, movie_link)

        # Convert the file to mkv if the user wants to and the file is an mp4
        file_ext = os.path.splitext(filename)[1]
        if self.convert_media.lower() == 'y':
            if file_ext == '.mp4':
                output_filename = os.path.splitext(filename)[0] + '.mkv'
                subprocess.check_output(['ffmpeg', '-i', filename, '-c', 'copy', output_filename], stderr=subprocess.STDOUT)
                filename = filename.replace('.mp4', '.mkv')
                os.remove(filename.replace('.mkv', '.mp4'))


    def get_filename(self, output, title, link):
        # Get the current filename of the media file from the output
        match = re.search(r'\[ffmpeg\] Merging formats into "(.*?)"', output)
        if match: 
            return match.group(1)
        else: 
            print(f'Error downloading {title} | url: {link}')


    def get_corresponding_season(self, url):
        """
        Returns the specific season that corresponds to the url
        """
        for season, link in self.season_dic.items():
            if link == url:
                return season


if __name__ == "__main__":
    DRTVScraper()
