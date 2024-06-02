import yfinance as yf  # Importing yfinance for fetching stock data
import pandas as pd  # Importing pandas for data manipulation
import numpy as np  # Importing numpy for numerical computations
import datetime  # Importing datetime for handling dates
from datetime import timedelta  # Importing timedelta for date arithmetic
from pandas_datareader import data as pdr  # Importing pandas_datareader for fetching stock data from Yahoo Finance
import time  # Importing time for time-related operations

# Override pandas_datareader's get_data_yahoo function to use yfinance
yf.pdr_override()

# Define the stock list and date for the study
stocklist = ["AAPL", "MSFT", "GOOGL", "TMDX", "HIMS", "SNX", "STEP", "AMG", "ANET", "ASR", "EURN", "GBDC", "HASI", "MAIN", "NVO", "OLED", "SPG", "UE", "UTHR", "VRTX", "WPM"]
# Example stock symbols
date_study = datetime.datetime.now()

# Initialize exportList DataFrame to store stock data that meets the criteria
exportList = pd.DataFrame(columns=["Stock", "RS_Rating", "currentClose", "20 Day MA", "50 Day MA", "70 Day MA", "150 Day MA", "200 Day MA", "52 Week Low", "52 week High"])
print("Initial exportList created")

# Initialize other variables
final = []  # List to store stocks that meet the criteria
index = []  # List to store index values of stocks that meet the criteria
rs = []  # List to store RS_Rating values of stocks that meet the criteria
stocks_fit_condition = 0  # Counter for stocks that meet the criteria
n = 0  # Counter for iteration over stocks

# Initialize counters
adv_w = 0  # Counter for stocks with advancing weekly close
decl_w = 0  # Counter for stocks with declining weekly close
adv = 0  # Counter for stocks with advancing daily close
decl = 0  # Counter for stocks with declining daily close

# Loop through each stock in the stock list
for stock in stocklist:
    print(f"Processing {stock}")
    n += 1
    start_date = date_study - timedelta(days=365)  # Start date for fetching stock data
    end_date = date_study  # End date for fetching stock data
    df = pdr.get_data_yahoo(stock, start=start_date, end=end_date)  # Fetch stock data from Yahoo Finance
    time.sleep(0.01)  # Pause to avoid hitting API limits

    try:
        # Calculate advancing and declining counts based on weekly close
        currentClose = df["Adj Close"].iloc[-1]
        lastweekClose = df["Adj Close"].iloc[-5]
        if currentClose > lastweekClose:
            adv_w += 1
        else:
            decl_w += 1
    except Exception as e:
        print(e)
    
    try:
        # Calculate advancing and declining counts based on daily close
        currentClose = df["Adj Close"].iloc[-1]
        yesterdayClose = df["Adj Close"].iloc[-2]
        if currentClose > yesterdayClose:
            adv += 1
        else:
            decl += 1
    except Exception as e:
        print(e)
    
    # Calculate closing prices for different time periods
    try:
        close_3m = df["Adj Close"].iloc[-63]
        close_6m = df["Adj Close"].iloc[-126]
        close_9m = df["Adj Close"].iloc[-189]
        close_12m = df["Adj Close"].iloc[-250]
        condition_ipo = False
    except Exception as e:
        condition_ipo = True  # Consider it is an IPO as no price can be found 1 year ago
        print(e)
    
    try:
        # Calculate turnover (Market Activity Indicator, High is Good)
        turnover = df["Volume"].iloc[-1] * df["Adj Close"].iloc[-1]
    except Exception as e:
        print(e)
    
    try:
        # Calculate true range for the last 10 days and last 5 days (Diff Between Prices)
        true_range_5d = (max(df["Adj Close"].iloc[-5:-1]) - min(df["Adj Close"].iloc[-5:-1]))
        true_range_10d = (max(df["Adj Close"].iloc[-10:-1]) - min(df["Adj Close"].iloc[-10:-1]))
    except Exception as e:
        print(e)
    
    try:
        # Calculate RS_Rating (Relative Strength Rating, Performance Indicator, High is Good)
        RS_Rating = (
            ((currentClose - close_3m) / close_3m) * 40 +
            ((currentClose - close_6m) / close_6m) * 20 +
            ((currentClose - close_9m) / close_9m) * 20 +
            ((currentClose - close_12m) / close_12m) * 20
        )
    except Exception as e:
        print(e)
    
    try:
        # Calculate various moving averages
        sma = [20, 50, 70, 150, 200]
        for x in sma:
            df["SMA_" + str(x)] = round(df.iloc[:, 4].rolling(window=x).mean(), 2)

        moving_average_20 = df["SMA_20"].iloc[-1]
        moving_average_50 = df["SMA_50"].iloc[-1]
        moving_average_70 = df["SMA_70"].iloc[-1]
        moving_average_150 = df["SMA_150"].iloc[-1]
        moving_average_200 = df["SMA_200"].iloc[-1]
        low_of_52week = min(df["Adj Close"].iloc[-260:])
        high_of_52week = max(df["Adj Close"].iloc[-260:])

        try:
            moving_average_200_20 = df["SMA_200"].iloc[-32]
        except Exception:
            moving_average_200_20 = 0

        # Condition checks for stock selection
        condition_1 = currentClose > moving_average_150 > moving_average_200
        condition_2 = moving_average_50 > moving_average_200
        condition_3 = moving_average_200 > moving_average_200_20 # 200 SMA trending up for at least 1 month (ideally 4-5 months)
        condition_4 = moving_average_50 > moving_average_150 > moving_average_200
        condition_5 = currentClose > moving_average_50
        condition_6 = currentClose >= (1.4 * low_of_52week)      # Current Price is at least 40% above 52 week low (Many of the best are up 100-300% before coming out of consolidation)
        condition_7 = currentClose >= (0.75 * high_of_52week)    # Current Price is within 25% of 52 week high
        condition_8 = turnover >= 1500000                        # Turnover is larger than 1.5 million
        condition_9 = true_range_10d < currentClose * 0.08       # True range in the last 10 days is less than 10% of current price
        condition_10 = currentClose > moving_average_20          # (optional)
        condition_11 = true_range_5d < currentClose * 6          # (optional) true range in the last 5 days is less than 6% of current price
        condition_12 = currentClose > 10

        # Check if all conditions are met
        if all([condition_1, condition_2, condition_3, condition_4, condition_5, condition_6, condition_7, condition_8, condition_9, condition_10, condition_11, condition_12]):
            final.append(stock)  # Add stock to final list
            index.append(n)  # Add index value to index list
            rs.append(RS_Rating)  # Add RS_Rating value to rs list
            stocks_fit_condition += 1  # Increment counter for stocks that meet the criteria

            # Append stock data to exportList DataFrame
            new_row = pd.DataFrame({
                'Stock': [stock], 
                "RS_Rating": [RS_Rating],
                "currentClose": [currentClose],
                "20 Day MA": [moving_average_20],
                "50 Day MA": [moving_average_50],
                "70 Day MA": [moving_average_70],
                "150 Day MA": [moving_average_150],
                "200 Day MA": [moving_average_200],
                "52 Week Low": [low_of_52week],
                "52 week High": [high_of_52week]
            })
            exportList = pd.concat([exportList, new_row], ignore_index=True)
            print(stock + " made the requirements")
            print(date_study)
    
    except Exception as e:
        print(e)
        print("No data on " + stock)

# Print the exportList containing stocks that meet the criteria
print(exportList)

# exportList:
#   Stock  RS_Rating  currentClose  20 Day MA  50 Day MA  70 Day MA  150 Day MA  200 Day MA  52 Week Low  52 week High
# 0  TMDX  76.830024    136.399994     134.86     106.18      99.14       85.81       78.24    36.740002    142.860001
# 1   SNX  32.148762    130.839996     125.33     118.69     114.31      106.86      104.46    88.765121    130.839996
# 2  EURN  32.569327     16.910000      15.55      13.98      13.86       13.80       13.54    10.622876     16.910000
# 3  GBDC  20.737418     16.570000      16.47      16.36      16.06       15.04       14.57    11.747225     17.123430
# 4  HASI  40.971764     33.290001      31.32      28.16      27.25       25.25       23.86    13.945637     33.330002
# 5   NVO  33.411865    135.279999     131.61     128.42     128.14      115.56      110.16    75.218002    136.039993
# 6   SPG  23.167488    151.309998     147.57     146.92     147.79      139.13      131.12   100.293304    156.490005
# 7  VRTX  21.995306    455.339996     434.29     416.08     416.81      405.60      392.67   324.649994    456.950012