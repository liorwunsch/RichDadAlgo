import yfinance as yf
import pandas as pd 
import numpy as np
import datetime
from datetime import timedelta
import time 
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

# Cumulative performance over the last `n` quarters
def calcQuarterPerformance(closes, n):
    length = min(len(closes), n * int(252 / 4)) # Calculate the number of trading days to consider, assuming 252 trading days per year
    prices = closes.tail(length)                # Get the closing prices for the last `length` days
    pct_chg = prices.pct_change().dropna()      # Compute the daily percentage changes in closing prices
    perf_cum = (pct_chg + 1).cumprod() - 1      # Calculate the cumulative performance
    return perf_cum.tail(1).item()              # Return the cumulative performance of the last day in this period

# Relative Strength (RS) Rating
def calcRsRating(data):
    closes = data['Adj Close']
    try:
        quarters1 = calcQuarterPerformance(closes, 1)
        quarters2 = calcQuarterPerformance(closes, 2)
        quarters3 = calcQuarterPerformance(closes, 3)
        quarters4 = calcQuarterPerformance(closes, 4)
        return 0.4*quarters1 + 0.2*quarters2 + 0.2*quarters3 + 0.2*quarters4
    except:
        return 0

# Earnings Per Share (EPS), a company's profitability per outstanding share of stock
def calcEPS(data):
    net_income = data.financials.loc['Net Income', :].iloc[0]  # Assuming we want the latest net income
    outstanding_shares = data.info['sharesOutstanding']
    earnings_per_share = net_income / outstanding_shares
    return earnings_per_share

# Earnings growth based on the net income from financial statements
def calcEarningsGrowth(financials):
    net_income  = financials.loc['Net Income']
    recent_earnings = net_income[0]
    year_ago_earnings = net_income[1]
    earnings_growth = ((recent_earnings - year_ago_earnings) / year_ago_earnings) * 100
    return earnings_growth

# Sales growth based on the total revenue from financial statements
def calcSalesGrowth(financials):
    sales = financials.loc['Total Revenue']
    recent_sales = sales[0]
    year_ago_sales = sales[1]
    sales_growth = ((recent_sales - year_ago_sales) / year_ago_sales) * 100
    return sales_growth

# Profit margin based on the most recent net income and total revenue
def calcProfitMargin(financials):
    sales = financials.loc['Total Revenue']
    earnings = financials.loc['Net Income']
    recent_sales = sales[0]
    recent_earnings = earnings[0]
    profit_margin = (recent_earnings / recent_sales) * 100
    return profit_margin

# Return on Equity (ROE), a company's profitability relative to shareholders' equity, based on the most recent net income and total stockholder equity
def calcROE(data):
    balance_sheet = data.balance_sheet
    shareholders_equity = balance_sheet.loc['Total Stockholder Equity']
    recent_earnings = data.financials.loc['Net Income'][0]
    recent_equity = shareholders_equity[0]
    roe = (recent_earnings / recent_equity) * 100
    return roe

# Composite Rating
def calcCompRating(data, rs_rating):
    earnings_growth = calcEarningsGrowth(data.financials)
    sales_growth = calcSalesGrowth(data.financials)
    profit_margin = calcProfitMargin(data.financials)
    roe = calcROE(data)
    return 0.25*rs_rating + 0.25*earnings_growth + 0.25*sales_growth + 0.125*profit_margin + 0.125*roe # Normalize and weight the metrics

def getFinancialRatings(data):
    rs_rating = calcRsRating(data)
    comp_rating = calcCompRating(data, rs_rating)
    eps = calcEPS(data)
    return rs_rating, comp_rating, eps

def minervini_trend_template_screener(stocklist):
    # Initialize exportList DataFrame to store stock data that meets the criteria
    exportList = pd.DataFrame(columns=["Stock", "RS_Rating", "Comp_Rating"])
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
    for symbol in stocklist:
        print(f"Processing {symbol}")
        n += 1

        hist = get_stock_data(symbol)

        print(hist)
        time.sleep(0.01)  # Pause to avoid hitting API limits

        rs_rating = calculate_rs_rating(hist)
        composite_rating = calcCompRating(symbol, rs_rating)

        try:
            # Calculate advancing and declining counts based on weekly close
            currentClose = hist["Adj Close"].iloc[-1] # -1 is for the last value
            lastweekClose = hist["Adj Close"].iloc[-5]
            if currentClose > lastweekClose:
                adv_w += 1
            else:
                decl_w += 1
        except Exception as e:
            print(e)

        try:
            # Calculate advancing and declining counts based on daily close
            currentClose = hist["Adj Close"].iloc[-1]
            yesterdayClose = hist["Adj Close"].iloc[-2]
            if currentClose > yesterdayClose:
                adv += 1
            else:
                decl += 1
        except Exception as e:
            print(e)

        try:
            # Calculate turnover (Market Activity Indicator, High is Good)
            turnover = hist["Volume"].iloc[-1] * hist["Adj Close"].iloc[-1]
        except Exception as e:
            print(e)

        try:
            # Calculate true range for the last 10 days and last 5 days (Diff Between Prices)
            true_range_5d = (max(hist["Adj Close"].iloc[-5:-1]) - min(hist["Adj Close"].iloc[-5:-1]))
            true_range_10d = (max(hist["Adj Close"].iloc[-10:-1]) - min(hist["Adj Close"].iloc[-10:-1]))
        except Exception as e:
            print(e)

        try:
            # Calculate various moving averages
            sma = [20, 50, 70, 150, 200]
            for x in sma:
                hist["SMA_" + str(x)] = round(hist.iloc[:, 4].rolling(window=x).mean(), 2)

            moving_average_20 = hist["SMA_20"].iloc[-1]
            moving_average_50 = hist["SMA_50"].iloc[-1]
            moving_average_70 = hist["SMA_70"].iloc[-1]
            moving_average_150 = hist["SMA_150"].iloc[-1]
            moving_average_200 = hist["SMA_200"].iloc[-1]
            low_of_52week = min(hist["Adj Close"].iloc[-252:])
            high_of_52week = max(hist["Adj Close"].iloc[-252:])

            try:
                moving_average_200_20 = hist["SMA_200"].iloc[-22]
            except Exception:
                moving_average_200_20 = 0

            # Condition checks for stock selection
            condition_1_1 = currentClose > moving_average_150        # Price > 150-day (30-week) MA
            condition_1_2 = currentClose > moving_average_200        # Price > 200-day (40-week) MA
            condition_2 = moving_average_150 > moving_average_200    # 150-day MA > 200-day MA
            condition_3 = moving_average_200 > moving_average_200_20 # 200-day MA trending up for at least 1 month (22 days)
            condition_4_1 = moving_average_50 > moving_average_150   # 50-day MA > 150-day MA
            condition_4_2 = moving_average_50 > moving_average_200   # 50-day MA > 200-day MA
            condition_5 = currentClose > moving_average_50           # Price above 50-day MA
            condition_6 = currentClose >= (1.25 * low_of_52week)     # Price at least 25% above 52-week low
            condition_7 = currentClose >= (0.75 * high_of_52week)    # Price within 25% of 52-week high

            # Check if all conditions are met
            if all([condition_1_1, condition_1_2, condition_2, condition_3, condition_4_1, condition_4_2, condition_5, condition_6, condition_7]):
                final.append(symbol)  # Add stock to final list
                index.append(n)  # Add index value to index list
                rs.append(rs_rating)  # Add RS_Rating value to rs list
                stocks_fit_condition += 1  # Increment counter for stocks that meet the criteria

                # Append stock data to exportList DataFrame
                new_row = pd.DataFrame({
                    'Stock': [symbol], 
                    "RS_Rating": [rs_rating],
                    "Comp_Rating": [composite_rating],
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
                print(symbol + " made the requirements")

        except Exception as e:
            print(e)
            print("No data on " + symbol)

    # Sort the exportList by RS_Rating in descending order
    exportList = exportList.sort_values(by="RS_Rating", ascending=False)
    print("Sorted exportList by RS_Rating:", exportList)

    # Save the results to CSV
    try:
        exportList.to_csv('Output/stocks.csv', index=False)
        print("CSV file created successfully")
    except Exception as e:
        print(e)
        print("Failed to create CSV file")

    return exportList

def detect_vcp_pattern_2(symbol):
    data = get_stock_data(symbol)

def detect_vcp_pattern(stock, rs_rating, composite_rating, window=5, volume_increase=2, price_increase=1.1):
    data = get_stock_data(symbol)

    # Ensure Date is a column in the DataFrame
    data.reset_index(inplace=True)
    data["Comp_Rating"] = composite_rating
    data["Comp_Rating>50"] = composite_rating > 50

    data["RS_Rating"] = rs_rating
    data["RS_Rating>55"] = rs_rating > 55

    # Calculate moving averages for price and volume
    data["MA_Price"] = data["Adj Close"].rolling(window=window).mean()
    data["MA_Volume"] = data["Volume"].rolling(window=window).mean()
    
    # Detect periods of relatively low volatility (price stable around MA_Price)
    data["Volatility"] = np.abs(data["Adj Close"] - data["MA_Price"]) / data["MA_Price"]
    data["Volatility<0.075"] = np.abs(data["Adj Close"] - data["MA_Price"]) / data["MA_Price"] < 0.075
    
    # Detect significant volume increase
    data["Volume_Increase"] = data["Volume"] / data["MA_Volume"]
    data["Volume_Increase>" + str(volume_increase)] = data["Volume_Increase"] > volume_increase
    
    # Detect significant price increase
    data["Price_Increase"] = data["Adj Close"] / data["Adj Close"].shift(1)
    data["Price_Increase>" + str(price_increase)] = data["Price_Increase"] > price_increase
    
    # Combine conditions to detect pre-burst pattern
    data["Pre_Burst_Pattern"] = data["Volatility<0.075"]
    data["Breakout"] = data["Price_Increase>" + str(price_increase)] & data["Volume_Increase>" + str(volume_increase)]

    return data

def should_i_buy_today_2():
    exportList = minervini_trend_template_screener(stocklist, date_study) # TODO - per day in the last year
    
    for index, row in exportList.iterrows():
        stock = row["Stock"]
        data = detect_vcp_pattern(stock, row["RS_Rating"], row["Comp_Rating"])
        print(stock, ":", data)

         # Get dates where the pattern was detected
        pattern_dates = data[data["Breakout"]]["Date"]

        #plotData(data, pattern_dates)

        # Save to Excel with the first row and first column frozen, adjusted column widths, and defined as a table
        output_filename = f"Output/{stock}.xlsx"
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name='PatternDates')
            worksheet = writer.sheets['PatternDates']
            worksheet.freeze_panes = 'B2'

            # Adjust column widths
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter  # Get the column name
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = max_length + 2  # Adding a little extra space
                worksheet.column_dimensions[column].width = adjusted_width

            # Define the table
            tab = Table(displayName="PatternTable", ref=f"A1:{get_column_letter(worksheet.max_column)}{worksheet.max_row}")

            # Add a default style with striped rows and banded columns
            style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=True)
            tab.tableStyleInfo = style
            worksheet.add_table(tab)

        print(f"Pattern dates saved to {output_filename}")


def is_trend_template(data):
    a = 1

def should_i_buy_today(symbol, date_study):
    one_year_ago = date_study - timedelta(days=365)
    data = yf.Ticker(symbol).history(start=one_year_ago, end=date_study)
    data.reset_index(inplace=True) # Ensure Date is a column in the DataFrame
    
    rs_rating, comp_rating, eps = getFinancialRatings(data)
    is_trend_template(data)

def main(stocklist):
    today_ = datetime.datetime.now()
    one_year_ago = today_ - timedelta(days=365)

    results = []
    for symbol in stocklist:
        date_study = one_year_ago
        while date_study <= today_:
            result = should_i_buy_today(symbol, date_study)
            results.append(result)
            date_study += timedelta(days=1)

# Define the stock list and date for the study
#stocklist = ["AAPL", "MSFT", "GOOGL", "TMDX", "HIMS", "SNX", "STEP", "AMG", "ANET", "ASR", "EURN", "GBDC", "HASI", "MAIN", "NVO", "OLED", "SPG", "UE", "UTHR", "VRTX", "WPM"]
stocklist = ["HIMS"]

main(stocklist)
