import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
from pandas_datareader import data as pdr
import time

yf.pdr_override()

# Define the stock list and date for the study
stocklist = ["AAPL", "MSFT", "GOOGL", "TMDX", "HIMS", "SNX", "STEP"]  # Example stock symbols
date_study = datetime.datetime.now()

# Initialize exportList DataFrame
exportList = pd.DataFrame(columns=["Stock", "RS_Rating", "50 Day MA", "150 Day MA", "200 Day MA", "52 Week Low", "52 week High"])
print("Initial exportList created")

# Initialize other variables
final = []
index = []
rs = []
stocks_fit_condition = 0
n = 0

# Initialize counters
adv_w = 0
decl_w = 0
adv = 0
decl = 0

# Loop through each stock in the stock list
for stock in stocklist:
    print(f"Processing {stock}")
    n += 1
    start_date = date_study - timedelta(days=365)
    end_date = date_study
    df = pdr.get_data_yahoo(stock, start=start_date, end=end_date)
    time.sleep(0.01)

    try:
        currentClose = df["Adj Close"].iloc[-1]
        lastweekClose = df["Adj Close"].iloc[-5]
        if currentClose > lastweekClose:
            adv_w += 1
        else:
            decl_w += 1
    except Exception as e:
        print(e)
    
    try:
        currentClose = df["Adj Close"].iloc[-1]
        yesterdayClose = df["Adj Close"].iloc[-2]
        if currentClose > yesterdayClose:
            adv += 1
        else:
            decl += 1
    except Exception as e:
        print(e)
    
    try:
        close_3m = df["Adj Close"].iloc[-63]
    except Exception as e:
        print(e)
    
    try:
        close_6m = df["Adj Close"].iloc[-126]
    except Exception as e:
        print(e)
    
    try:
        close_9m = df["Adj Close"].iloc[-189]
    except Exception as e:
        print(e)
    
    try:
        close_12m = df["Adj Close"].iloc[-250]
        condition_ipo = False
    except Exception as e:
        condition_ipo = True  # Consider it is an IPO as no price can be found 1 year ago
        print(e)
    
    try:
        turnover = df["Volume"].iloc[-1] * df["Adj Close"].iloc[-1]
    except Exception as e:
        print(e)
    
    try:
        true_range_10d = (max(df["Adj Close"].iloc[-10:-1]) - min(df["Adj Close"].iloc[-10:-1]))
    except Exception as e:
        print(e)
    
    try:
        RS_Rating = (
            ((currentClose - close_3m) / close_3m) * 40 +
            ((currentClose - close_6m) / close_6m) * 20 +
            ((currentClose - close_9m) / close_9m) * 20 +
            ((currentClose - close_12m) / close_12m) * 20
        )
    except Exception as e:
        print(e)
    
    try:
        sma = [20, 50, 150, 200]
        for x in sma:
            df["SMA_" + str(x)] = round(df.iloc[:, 4].rolling(window=x).mean(), 2)

        moving_average_20 = df["SMA_20"].iloc[-1]
        moving_average_50 = df["SMA_50"].iloc[-1]
        moving_average_150 = df["SMA_150"].iloc[-1]
        moving_average_200 = df["SMA_200"].iloc[-1]
        low_of_52week = min(df["Adj Close"].iloc[-260:])
        high_of_52week = max(df["Adj Close"].iloc[-260:])

        try:
            moving_average_200_20 = df["SMA_200"].iloc[-32]
        except Exception:
            moving_average_200_20 = 0

        # Condition checks
        condition_1 = currentClose > moving_average_150 > moving_average_200
        condition_2 = moving_average_50 > moving_average_200
        condition_3 = moving_average_200 > moving_average_200_20
        condition_4 = moving_average_50 > moving_average_150 > moving_average_200
        condition_5 = currentClose > moving_average_50
        condition_6 = currentClose >= (1.4 * low_of_52week)
        condition_7 = currentClose >= (0.75 * high_of_52week)
        condition_8 = turnover >= 1500000
        condition_9 = true_range_10d < currentClose * 0.08
        condition_10 = currentClose > moving_average_20
        condition_12 = currentClose > 10

        if all([condition_1, condition_2, condition_3, condition_4, condition_5, condition_6, condition_7, condition_8, condition_9, condition_12]):
            final.append(stock)
            index.append(n)
            rs.append(RS_Rating)
            stocks_fit_condition += 1

            new_row = pd.DataFrame({
                'Stock': [stock], 
                "RS_Rating": [RS_Rating],
                "50 Day MA": [moving_average_50],
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

print(exportList)

# exportList:
#    Stock  RS_Rating  50 Day MA  150 Day MA  200 Day MA  52 Week Low  52 week High
# 0  GOOGL  30.490128     162.86      146.49      143.46   116.449997    177.850006
# 1   TMDX  76.830024     106.18       85.81       78.24    36.740002    142.860001
# 2    SNX  32.148764     118.69      106.86      104.46    88.765114    130.839996