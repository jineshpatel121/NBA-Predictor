import os
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO

SCORE_DIR = "data/scores"

boxScores = os.listdir(SCORE_DIR)

# Join the file name and the actual file to "boxScore"
boxScores = [os.path.join(SCORE_DIR, f) for f in boxScores if f.endswith(".html")]

def parseHtml(boxScore):
    with open(boxScore) as f:
        html = f.read()
    soup = BeautifulSoup(html)

    # Remove empty space above column headers, for easier parsing by pandas
    [s.decompose() for s in soup.select("tr.over_header")]
    [s.decompose() for s in soup.select("tr.thead")]
    return soup
    

def readLineScore(soup):
    # Convert the soup object to a string and wrap it in a StringIO object
    lineScore = pd.read_html(StringIO(str(soup)), attrs={"id": "line_score"})[0]
    cols = list(lineScore.columns)
    cols[0] = "team"
    cols[-1] = "total"
    lineScore.columns = cols
    
    # Remove the quarterly score breakdown, just keep total score 
    lineScore = lineScore[["team", "total"]]
    return lineScore

    

from io import StringIO

def readStats(soup, team, stat):
    # Convert the soup object to a string and wrap it in a StringIO object
    html_string = StringIO(str(soup))
    df = pd.read_html(html_string, attrs={"id": f"box-{team}-game-{stat}"}, index_col=0)[0]
    df = df.apply(pd.to_numeric, errors="coerce")
    return df


def readSzn(soup):
    nav = soup.select("#bottom_nav_container")[0]
    hrefs = [a["href"] for a in nav.find_all("a")]
    season = os.path.basename(hrefs[1]).split("_")[0]
    return season

baseCols = None
games = []

for boxScore in boxScores:
    soup = parseHtml(boxScore)
    lineScore = readLineScore(soup)
    teams = list(lineScore["team"])

    summaries = []

    for team in teams:
        basic = readStats(soup, team, "basic")
        advanced = readStats(soup, team, "advanced")
    
        total = pd.concat([basic.iloc[-1, :], advanced.iloc[-1, :]])
        total.index = total.index.str.lower()
    
        # Highest singular stats
        maxes = pd.concat([basic.iloc[:-1].max(), advanced.iloc[:-1].max()])
        maxes.index = maxes.index.str.lower() + "_max"
    
        summary = pd.concat([total, maxes])
    
        if baseCols is None:
            baseCols = list(summary.index.drop_duplicates(keep="first"))
            baseCols = [b for b in baseCols if "bpm" not in b]
    
        summary = summary[baseCols]
        summaries.append(summary)
    
    summary = pd.concat(summaries, axis=1).T
    game = pd.concat([summary, lineScore], axis=1)
    
    game["home"] = [0, 1]
    gameOpp = game.iloc[::-1].reset_index(drop=True)
    gameOpp.columns += "_opp"
    
    fullGame = pd.concat([game, gameOpp], axis=1)
    
    fullGame["season"] = readSzn(soup)
    fullGame["date"] = os.path.basename(boxScore)[:8]
    fullGame["date"] = pd.to_datetime(fullGame["date"], format="%Y%m%d")
    fullGame["won"] = fullGame["total"] > fullGame["total_opp"]
    
    games.append(fullGame)

    if len(games) % 100 == 0:
        print(f"{len(games)} / {len(boxScores)}")

games_df = pd.concat(games, ignore_index = True)
