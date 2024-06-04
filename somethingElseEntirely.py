import yfinance as yf  # Importing yfinance for fetching stock data
import pandas as pd  # Importing pandas for data manipulation
import numpy as np  # Importing numpy for numerical computations
import datetime  # Importing datetime for handling dates
from datetime import timedelta  # Importing timedelta for date arithmetic
from pandas_datareader import data as pdr  # Importing pandas_datareader for fetching stock data from Yahoo Finance
import time  # Importing time for time-related operations

def screener(stocklist, date_study):
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
        print(df)
        time.sleep(0.01)  # Pause to avoid hitting API limits

        try:
            # Calculate advancing and declining counts based on weekly close
            currentClose = df["Adj Close"].iloc[-1] # -1 is for the last value
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
            condition_10 = True #currentClose > moving_average_20          # (optional)
            condition_11 = True #true_range_5d < currentClose * 6          # (optional) true range in the last 5 days is less than 6% of current price
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

    # Save the results to CSV
    try:
        exportList.to_csv('stocks.csv', index=False)
        print("CSV file created successfully")
    except Exception as e:
        print(e)
        print("Failed to create CSV file")

    return exportList

def detect_vcp_breakout(stock, date_study, volume_threshold=1.05):
    start_date = date_study - timedelta(days=365)                   # Start date for fetching stock data
    end_date = date_study                                           # End date for fetching stock data
    df = pdr.get_data_yahoo(stock, start=start_date, end=end_date)  # Fetch stock data from Yahoo Finance
    
    # Find local extrema
    df["is_local_max"] = (df["Adj Close"] > df["Adj Close"].shift(1)) & (df["Adj Close"] > df["Adj Close"].shift(-1))
    df["is_local_min"] = (df["Adj Close"] < df["Adj Close"].shift(1)) & (df["Adj Close"] < df["Adj Close"].shift(-1))
    
    # Get dates of local extrema
    extrema_dates = df.index[df["is_local_min"]]

    print("Adj Close: ", df["Adj Close"])
    print("is_local_max: ", df["is_local_max"])
    print("is_local_min: ", df["is_local_min"])
    print("exterme_dates: ", extrema_dates)
    
    # Calculate time intervals between extrema
    time_intervals = extrema_dates.diff().dropna().days
    print("time_intervals: ", time_intervals)
    
    # Check if time intervals are decreasing
    decreasing_intervals = all(x > y for x, y in zip(time_intervals, time_intervals[1:]))

    breakout_dates = []
    if decreasing_intervals:
        # Check for breakout in price and volume
        breakout = df[(df["Volume"] > df["Volume"].shift(1) * volume_threshold)]
        if not breakout.empty:
            # Append all breakout dates to the list
            breakout_dates.extend(breakout.index.tolist())
    
    if breakout_dates:
        return breakout_dates
    else:
        return 'No breakout detected'

def main():
    # Override pandas_datareader's get_data_yahoo function to use yfinance
    yf.pdr_override()

    # Today
    date_study = datetime.datetime.now()

    # Define the stock list and date for the study
    #stocklist = ["AAPL", "MSFT", "GOOGL", "TMDX", "HIMS", "SNX", "STEP", "AMG", "ANET", "ASR", "EURN", "GBDC", "HASI", "MAIN", "NVO", "OLED", "SPG", "UE", "UTHR", "VRTX", "WPM"]
    stocklist = ["TMDX"]

    exportList = screener(stocklist, date_study)

    # Print the exportList containing stocks that meet the criteria
    print(exportList)

    for index, row in exportList.iterrows():
        stock = row['Stock']
        breakout_dates = detect_vcp_breakout(stock, date_study)
        print(stock + ": " + breakout_dates)

main()
