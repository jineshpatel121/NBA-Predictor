NBA Game Predictor

This project is a machine learning-based NBA game predictor. It includes a web scraper, data reformatting script, and a model for predicting outcomes of NBA games.

Project Structure

- nbaScraper.py: This script scrapes data for a couple of NBA seasons from Basketball Reference. The scraping process is currently retirves 2 seasons worth of data, but the number of seaosns can easily be modified.
  
- reformatNbaData.py: This script reformats the raw scraped data into a usable format for analysis and prediction.

- predictNBA.py: This script implements the machine learning model. It loads the dataset, processes the data, and uses it to predict the outcomes of NBA games.

- nba_games.csv: This CSV file contains data for all NBA seasons. It serves as the primary dataset for building and training the prediction model.

- nba2023_500Data.csv: This CSV file contains data for the 2022-2023. It serves as a smaller dataset to check functionality of the web scraper script.

Getting Started

Prerequisites:

To run this project, you'll need:

- Python 3.x
- pandas
- scikit-learn
- requests (for web scraping)
  
Running the Project

1. Data Scraping:
   - Run nbaScraper.py to scrape NBA data for a number of seasons.
   - Alternatively, use the provided nba_games.csv for the full dataset of all NBA seasons.


2. Reformat Data:
   - Use reformatNbaData.py to reformat the raw data if you are using the scraped data instead of the CSV.


3. Make Predictions:
   - Run predictNBA.py to predict the outcomes of NBA games using the machine learning model.


Future Work

- Extend the model to also consider individual player statics as well as overall team data.
- Improve the prediction accuracy by refining the model and exploring additional features that allow user input.
