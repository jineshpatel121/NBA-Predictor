import pandas as pd
from sklearn.linear_model import RidgeClassifier
from sklearn.feature_selection import SequentialFeatureSelector
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score

# Load data
df = pd.read_csv("nba_games.csv", index_col=0)

# Sort by date and re-order index
df = df.sort_values("date").reset_index(drop=True)

# Remove repetitive columns
del df["mp.1"]
del df["mp_opp.1"]
del df["index_opp"]

# Create target column using pd.concat to avoid fragmentation
def add_target(group):
    target_col = group["won"].shift(-1)
    return pd.concat([group, target_col.rename("target")], axis=1).reset_index(drop=True)

# Group by team but reset the index to avoid 'team' becoming the index
df = df.groupby("team", group_keys=False).apply(add_target)

# Handle NaN values in 'target' column
df.loc[pd.isnull(df["target"]), "target"] = 2
df["target"] = df["target"].astype(int, errors="ignore")

# Remove columns with nulls
nulls = pd.isnull(df).sum()
valid_columns = df.columns[~df.columns.isin(nulls[nulls > 0].index)]
df = df[valid_columns].copy()

# Initialize model and feature selector
rr = RidgeClassifier(alpha=1)
split = TimeSeriesSplit(n_splits=3)
sfs = SequentialFeatureSelector(rr, n_features_to_select = 30, direction="forward", cv=split, n_jobs=1)

# Select columns for scaling and model fitting
removeCols = ["season", "date", "won", "target", "team", "team_opp"]
scaleCols = df.columns[~df.columns.isin(removeCols)]

# Scale selected columns
scaler = MinMaxScaler()
df[scaleCols] = scaler.fit_transform(df[scaleCols])

# Fit Sequential Feature Selector
sfs.fit(df[scaleCols], df["target"])
predictors = list(scaleCols[sfs.get_support()])

# Define backtest function
def backtest(data, model, predictors, start=2, step=1):
    allPreds = []
    seasons = sorted(data["season"].unique())

    for i in range(start, len(seasons), step):
        season = seasons[i]
        train = data[data["season"] < season]
        test = data[data["season"] == season]

        model.fit(train[predictors], train["target"])
        preds = model.predict(test[predictors])
        preds = pd.Series(preds, index=test.index)

        combined = pd.concat([test["target"], preds], axis=1)
        combined.columns = ["actual", "prediction"]
        allPreds.append(combined)

    return pd.concat(allPreds)

# Run backtest and check accuracy
predictions = backtest(df, rr, predictors)
score = accuracy_score(predictions["actual"], predictions["prediction"])


print(predictions)
print(f"Base Model Accuracy: {score * 100}%")

# Rolling averages calculation
dfRolling = df[list(scaleCols) + ["won", "team", "season"]]

# Reset the index, ensuring that 'team' doesn't cause ambiguity
dfRolling = dfRolling.reset_index(drop=True)

def find_team_averages(team):
    numeric_cols = team.select_dtypes(include=[float, int]).columns
    rolling = team[numeric_cols].rolling(10).mean().reset_index(drop=True)
    return rolling

# Calculate rolling averages for each team and season
dfRolling = dfRolling.groupby(["team", "season"], group_keys=False).apply(find_team_averages)

# Rename rolling columns
rollingCols = [f"{col}_Roll" for col in dfRolling.columns]
dfRolling.columns = rollingCols

# Reset index for both dataframes before concatenation
df = df.reset_index(drop=True)
dfRolling = dfRolling.reset_index(drop=True)

# Merge rolling averages and drop missing values
df = pd.concat([df, dfRolling], axis=1).dropna()

# Shift columns for next game info
def shift_col(team, col_name):
    return team[col_name].shift(-1).reset_index(drop=True)

def add_col(df, col_name):
    return df.groupby("team", group_keys=False).apply(lambda x: shift_col(x, col_name)).reset_index(drop=True)
    
df["home_next"] = add_col(df, "home")
df["team_opp_next"] = add_col(df, "team_opp")
df["date_next"] = add_col(df, "date")

# Merge with opponent's next game info
fullDf = df.merge(df[rollingCols + ["team_opp_next", "date_next", "team"]],
                left_on=["team", "date_next"], right_on=["team_opp_next", "date_next"])

# Update removed columns
removeCols = list(fullDf.columns[fullDf.dtypes == "object"]) + removeCols
scaleCols = fullDf.columns[~fullDf.columns.isin(removeCols)]

# Fit Sequential Feature Selector on the full dataset
sfs.fit(fullDf[scaleCols], fullDf["target"])
predictors = list(scaleCols[sfs.get_support()])

# Run backtest on the full dataset and check accuracy
predictions = backtest(fullDf, rr, predictors)
score = accuracy_score(predictions["actual"], predictions["prediction"])

print(predictions)
print(f"Rolling Avg Model Accuracy: {score * 100}%")