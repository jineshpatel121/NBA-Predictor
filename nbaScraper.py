import os
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import time

SEASONS = list(range(2022, 2024))

DATA_DIR = "data"
STANDINGS_DIR = os.path.join(DATA_DIR, "standings")
SCORES_DIR = os.path.join(DATA_DIR, "scores")


async def getHtml(url, selector, sleep=5, retries=3):
    html = None         

    # Search for html at least 3 times
    for i in range(1, retries + 1):
        # Slows the program so we don't get banned
        time.sleep(sleep * i)
        try:
            # Initialize playwright
            async with async_playwright() as p:
                # Launch browser and wait until it launches (makes it sync)
                browser = await p.chromium.launch(timeout=60000)  # Increase timeout to 60 seconds
                page = await browser.new_page()
                await page.goto(url)
                print(await page.title())
                html = await page.inner_html(selector)
        # When timeout error occurs...
        except PlaywrightTimeout:
            print(f"Timeout error on {url}")
            continue
        # If no timeout error, end search
        else:
            break
    return html


async def scrapeSzn(season):
    url = f"https://www.basketball-reference.com/leagues/NBA_{season}_games.html"
    # Get link for each month 
    html = await getHtml(url, "#content .filter")
    
    if not html:
        print(f"Failed to fetch HTML for season {season}")
        return  # Skip this season if we cannot get HTML

    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all("a")
    href = [l["href"] for l in links]
    # Full links
    standingPage = [f"https://www.basketball-reference.com{l}" for l in href]

    for url in standingPage:
        save_path = os.path.join(STANDINGS_DIR, url.split("/")[-1])
        # Make sure not to re-scrape
        if os.path.exists(save_path):
            continue
        html = await getHtml(url, "#all_schedule")
        
        if not html:
            print(f"Failed to fetch HTML for {url}")
            continue  # Skip this URL if the HTML is not fetched
        
        # Write links into a file
        with open(save_path, "w+") as f:
            f.write(html)

# Ensure async context is respected
async def main():
    for season in (SEASONS):
        await scrapeSzn(season)

    standingFiles = [s for s in os.listdir(STANDINGS_DIR) if ".html" in s]
    
    async def scrapeGame(standingFile):
        with open(standingFile, 'r') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all("a")
        hrefs = [l.get("href") for l in links]
        boxScores = [l for l in hrefs if l and "boxscore" in l and ".html" in l]
        boxScores = [f"https://www.basketball-reference.com{l}" for l in boxScores]

        for url in boxScores:
            save_path = os.path.join(SCORES_DIR, url.split("/")[-1])
            if os.path.exists(save_path):
                continue

            html = await getHtml(url, "#content")
            if not html:
                continue
            with open(save_path, "w+") as f:
                f.write(html)
    
    for f in standingFiles:
        filePath = os.path.join(STANDINGS_DIR, f)
        await scrapeGame(filePath)

# Run the script
await main()
