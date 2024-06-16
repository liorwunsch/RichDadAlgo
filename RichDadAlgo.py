import sys
import yfinance as yf
import pandas as pd 
import numpy as np
import math
import datetime
from datetime import timedelta
import time
import pytz
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
import os
import shutil

def readStockList():
    file_name = 'stocks.txt'
    with open(file_name, 'r') as file:
        stocklist = file.readlines()
    stocklist = [line.strip() for line in stocklist] # Remove newline characters from each line
    stocklist = list(set(stocklist))
    stocklist.sort()

    print(stocklist)
    return stocklist

def createOutputFolder():
    folder_name = "Output"
    try:
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        os.makedirs(folder_name)
    except:
        print("CANNOT OPEN FOLDER: ", folder_name)
        return False
    return True
    
# Save to Excel with the first row and first column frozen, adjusted column widths, and defined as a table
def printToExcel(file_name, results=pd.DataFrame()):
    if results.empty:
        print("printToExcel: " + file_name + "'s results is empty")
        return

    output_filename = f"Output/{file_name}.xlsx"
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        if "Date" in results.columns:
            results['Date'] = results['Date'].dt.tz_localize(None)
        
        results.to_excel(writer, index=False, sheet_name='results')
        worksheet = writer.sheets['results']
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
        tab = Table(displayName="results", ref=f"A1:{get_column_letter(worksheet.max_column)}{worksheet.max_row}")
        # Add a default style with striped rows and banded columns
        style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=True)
        tab.tableStyleInfo = style
        worksheet.add_table(tab)
    print(f"results saved to {output_filename}")

def getLastCloseDate(tz, ny_close_hour=16, ny_close_minute=0):
    tz1 = pytz.timezone(tz)
    tz2 = pytz.timezone('America/New_York')
    _today = datetime.datetime.now()
    time1 = tz1.localize(_today)
    time2 = tz2.localize(_today)
    time_difference = (time2 - time1).total_seconds() / 3600
    time_difference_hours = math.floor(time_difference)
    time_difference_minutes = (int)((time_difference - time_difference_hours) * 60)

    # NYSE and NASDAQ After Hours at TimeZone tz
    close_time = datetime.datetime(_today.year, _today.month, _today.day, ny_close_hour, ny_close_minute)
    local_close_time = close_time + timedelta(hours=time_difference_hours, minutes=(time_difference_minutes + 1))

    if _today < local_close_time:
        _today = local_close_time - timedelta(days=1)
    else:
        _today = local_close_time

    _today = _today.replace(hour=0, minute=0)
    #print(f"last_close_date = {_today}")
    return _today

# Determine dates when the stock exchange was open so calculation won't have duplicates
def determineActiveDates(symbol, start_date, end_date):
    data = yf.Ticker(symbol)
    hist = data.history(start=start_date, end=end_date+timedelta(days=1)) # +1 for data of today's afterhours and not yesterday's
    hist = hist.drop_duplicates()

    active_dates = hist.index
    active_dates = active_dates.tolist()
    #print(f"end_date = {end_date}")
    #print(f"active_dates = {active_dates}")
    #sys.exit()
    return active_dates

# Cumulative performance over the last `n` quarters
def calcQuarterPerformance(closes, n):
    length = min(len(closes), n * int(252 / 4)) # Calculate the number of trading days to consider, assuming 252 trading days per year
    prices = closes.tail(length)                # Get the closing prices for the last `length` days
    pct_chg = prices.pct_change().dropna()      # Compute the daily percentage changes in closing prices
    perf_cum = (pct_chg + 1).cumprod() - 1      # Calculate the cumulative performance

    quarter_performance = perf_cum.tail(1).item()              # Return the cumulative performance of the last day in this period
    return quarter_performance

# Relative Strength (RS) Rating
def calcRsRating(hist):
    closes = hist["Close"].iloc[-252:]
    try:
        quarters1 = calcQuarterPerformance(closes, 1)
        quarters2 = calcQuarterPerformance(closes, 2)
        quarters3 = calcQuarterPerformance(closes, 3)
        quarters4 = calcQuarterPerformance(closes, 4)
        rs_rating = (0.4*quarters1 + 0.2*quarters2 + 0.2*quarters3 + 0.2*quarters4) * 100
    except:
        rs_rating = 0

    return rs_rating

# Earnings Per Share (EPS), a company's profitability per outstanding share of stock
def calcEPS(financials, stock_info):
    net_income = financials.loc['Net Income', :].iloc[0]  # Assuming we want the latest net income
    outstanding_shares = stock_info['sharesOutstanding']

    earnings_per_share = net_income / outstanding_shares
    return earnings_per_share

# Earnings growth based on the net income from financial statements
def calcEarningsGrowth(financials):
    net_income  = financials.loc['Net Income']
    recent_earnings = net_income.iloc[0]
    year_ago_earnings = net_income.iloc[1]

    earnings_growth = ((recent_earnings - year_ago_earnings) / year_ago_earnings) * 100
    return earnings_growth

# Sales growth based on the total revenue from financial statements
def calcSalesGrowth(financials):
    sales = financials.loc['Total Revenue']
    recent_sales = sales.iloc[0]
    year_ago_sales = sales.iloc[1]

    sales_growth = ((recent_sales - year_ago_sales) / year_ago_sales) * 100
    return sales_growth

# Profit margin based on the most recent net income and total revenue
def calcProfitMargin(financials):
    sales = financials.loc['Total Revenue']
    earnings = financials.loc['Net Income']
    recent_sales = sales.iloc[0]
    recent_earnings = earnings.iloc[0]

    profit_margin = (recent_earnings / recent_sales) * 100
    return profit_margin

# Return on Equity (ROE), a company's profitability relative to shareholders' equity, based on the most recent net income and total stockholder equity
def calcROE(financials, balance_sheet):
    shareholders_equity = balance_sheet.loc['Stockholders Equity'].iloc[0]
    net_income = financials.loc['Net Income'].iloc[0]

    roe = (net_income / shareholders_equity) * 100
    return roe

# Composite Rating
def calcCompRating(financials, balance_sheet, rs_rating):
    earnings_growth = calcEarningsGrowth(financials)
    sales_growth = calcSalesGrowth(financials)
    profit_margin = calcProfitMargin(financials)
    roe = calcROE(financials, balance_sheet)

    comp_rating = 0.25*rs_rating + 0.25*earnings_growth + 0.25*sales_growth + 0.125*profit_margin + 0.125*roe # Normalize and weight the metrics
    return comp_rating

def getFinancialRatings(hist, financials, balance_sheet, stock_info):
    rs_rating = calcRsRating(hist)
    comp_rating = calcCompRating(financials, balance_sheet, rs_rating)
    eps = calcEPS(financials, stock_info)

    return rs_rating, comp_rating, eps

def calcCurrentMovingAverages(data):
    sma = [20, 50, 70, 150, 200]
    for x in sma:
        data["SMA_" + str(x)] = round(data.iloc[:, 4].rolling(window=x).mean(), 2)
                                      
    ma_20 = data["SMA_20"].iloc[-1]
    ma_50 = data["SMA_50"].iloc[-1]
    ma_70 = data["SMA_70"].iloc[-1]
    ma_150 = data["SMA_150"].iloc[-1]
    ma_200 = data["SMA_200"].iloc[-1]
    ma_200_20 = data["SMA_200"].iloc[-22]

    return ma_20, ma_50, ma_70, ma_150, ma_200, ma_200_20

def isTrendTemplateSimple(hist):
    close = hist["Close"].iloc[-1] # -1 is for the last value

    ma_20, ma_50, ma_70, ma_150, ma_200, ma_200_20 = calcCurrentMovingAverages(hist)
    
    high_of_52week = max(hist["Close"].iloc[-252:])
    low_of_52week = min(hist["Close"].iloc[-252:])

    # Condition checks for stock selection
    condition_1_1 = close > ma_150                 # Price > 150-day (30-week) MA
    condition_1_2 = close > ma_200                 # Price > 200-day (40-week) MA
    condition_2 = ma_150 > ma_200                  # 150-day MA > 200-day MA
    condition_3 = ma_200 > ma_200_20               # 200-day MA trending up for at least 1 month (22 days)
    condition_4_1 = ma_50 > ma_150                 # 50-day MA > 150-day MA
    condition_4_2 = ma_50 > ma_200                 # 50-day MA > 200-day MA
    condition_5 = close > ma_50                    # Price above 50-day MA
    condition_6 = close >= (0.75 * high_of_52week) # Price within 25% of 52-week high
    condition_7 = close >= (1.25 * low_of_52week)  # Price at least 25% above 52-week low

    is_trend_template = condition_1_1 & condition_1_2 & condition_2 & condition_3 & condition_4_1 & condition_4_2 & condition_5 & condition_6 & condition_7
    return is_trend_template

def isTrendTemplateExponential(data, date_study):
    two_year_ago = date_study - timedelta(days=730)
    hist = data.history(start=two_year_ago, end=date_study+timedelta(days=1)) # +1 for data of today's afterhours and not yesterday's
    hist = hist.drop_duplicates()
    hist.reset_index(inplace=True) # Ensure Date is a column in the DataFrame
    if not isinstance(hist.index, pd.DatetimeIndex): # Ensure the index is a DatetimeIndex
        hist.index = pd.to_datetime(hist["Date"])
    
    hist['EMA50'] = hist['Close'].ewm(span=50, adjust=False).mean()
    hist['EMA150'] = hist['Close'].ewm(span=150, adjust=False).mean()
    hist['EMA200'] = hist['Close'].ewm(span=200, adjust=False).mean()
    hist['EMA200_back1m'] = hist['EMA200'].shift(21)
    hist['vEMA20'] = hist['Volume'].ewm(span=20, adjust=False).mean()

    # Weekly
    week_hist = hist['Close'].resample('W').ohlc() # week ending on sunday
    week_hist['Low_1'] = hist['Low'].resample('W').min()
    week_hist.reset_index(inplace=True) # Ensure Date is a column in the DataFrame
    if not isinstance(week_hist.index, pd.DatetimeIndex): # Ensure the index is a DatetimeIndex
        week_hist.index = pd.to_datetime(week_hist["Date"])
    
    #print("data['Low'] = ", data['Low'])
    #print("data['High'] = ", data['High'])
    #print("weekly_data = ", weekly_data)
    #sys.exit()

    weekly_max = week_hist['close'].rolling(window=52).max() # max close over 52 weeks
    weekly_min = week_hist['Low_1'].rolling(window=52).min() # min low over 52 weeks

    # first of two_years_ago not needed anymore
    week_hist = week_hist.iloc[51:]
    hist = hist.iloc[251:]

    week_hist['Bracket_Max'] = weekly_max * 1.25
    week_hist['Bracket_Min'] = weekly_min * 1.3

    #printToExcel("weekly_hist", week_hist)
    #sys.exit()

    #week_hist.at[week_hist.index[0], 'Bracket_Max'] = 123

    # Resample weekly data to daily and forward fill to align with daily data
    daily_bracket_max = week_hist['Bracket_Max'].resample('D').ffill()
    daily_bracket_min = week_hist['Bracket_Min'].resample('D').ffill()

    #print("daily_bracket_max = ", daily_bracket_max)
    #print("daily_bracket_min = ", daily_bracket_min)
    #sys.exit()

    # Align the length of daily_bracket_* with data['Close']
    hist['daily_bracket_max'] = daily_bracket_max.reindex(hist.index, method='ffill')
    hist['daily_bracket_min'] = daily_bracket_min.reindex(hist.index, method='ffill')

    #print('daily_bracket_max after = ', daily_bracket_max)
    #print('daily_bracket_min after = ', daily_bracket_min)
    #sys.exit()

    condition_1 = hist['Close'] >= hist['EMA150']
    condition_2 = hist['Close'] >= hist['EMA200']
    condition_3 = hist['EMA150'] >= hist['EMA200']
    condition_4 = hist['EMA200'] > hist['EMA200_back1m']
    condition_5 = hist['EMA50'] > hist['EMA150']
    condition_6 = hist['EMA50'] > hist['EMA200']
    condition_7 = hist['Close'] > hist['EMA50']
    condition_8 = hist['Close'] <= hist['daily_bracket_max']
    condition_9 = hist['Close'] >= hist['daily_bracket_min']
    condition_10 = hist["Volume"] >= hist['vEMA20']

    is_trend_template_exp = condition_1 & condition_2 & condition_3 & condition_4 & condition_5 & condition_6 & condition_7 & condition_8 & condition_9 & condition_10
    #hist['is_trend_template_exp'] = is_trend_template_exp
    #printToExcel("hist", hist)
    #sys.exit()

    #screened_data = data[is_trend_template_exp]
    return is_trend_template_exp

def isTrendTemplate(data, hist, date_study, is_exponential):
    if not is_exponential:
        return isTrendTemplateSimple(hist)
    return isTrendTemplateExponential(data, date_study)

# **5** trading days Back
def isVCP(hist, _window=5, volume_increase_condition=1.75, price_increase_condition=1.05):
    # Ensure Date is a column in the DataFrame
    hist.reset_index(inplace=True)

    # Calculate moving averages for price and volume
    hist["MA_Price"] = hist["Close"].rolling(window=_window).mean()
    hist["MA_Volume"] = hist["Volume"].rolling(window=_window).mean()
    
    # Detect periods of relatively low volatility (price stable around MA_Price)
    hist["Volatility"] = np.abs(hist["Close"] - hist["MA_Price"]) / hist["MA_Price"]
    hist["Volatility<0.075"] = hist["Volatility"] < 0.075
    
    # Detect significant volume increase
    hist["Volume_Increase"] = hist["Volume"] / hist["MA_Volume"]
    hist["Volume_Increase>" + str(volume_increase_condition)] = hist["Volume_Increase"] > volume_increase_condition
    
    # Detect significant price increase
    hist["Price_Increase"] = hist["Close"] / hist["Close"].shift(1)
    hist["Price_Increase>" + str(price_increase_condition)] = hist["Price_Increase"] > price_increase_condition
    
    # Combine conditions to detect pre-burst (vcp) pattern
    hist["Pre_Burst_Pattern"] = hist["Volatility<0.075"]
    hist["Breakout"] = hist["Price_Increase>" + str(price_increase_condition)] & hist["Volume_Increase>" + str(volume_increase_condition)]

    is_vcp_pattern = hist["Pre_Burst_Pattern"].iloc[-1]
    is_vcp_breakout = hist["Breakout"].iloc[-1]
    price_increase = hist["Price_Increase"].iloc[-1]
    volume_increase = hist["Volume_Increase"].iloc[-1]
    return is_vcp_pattern, is_vcp_breakout, price_increase, volume_increase

def getKpiAtDay(symbol, date_study, b_check_trend_exponential):
    one_year_ago = date_study - timedelta(days=365)
    data = yf.Ticker(symbol)
    
    financials = data.financials
    balance_sheet = data.balance_sheet
    stock_info = data.info
    hist = data.history(start=one_year_ago, end=date_study+timedelta(days=1)) # +1 for data of today's afterhours and not yesterday's
    hist = hist.drop_duplicates()
    hist.reset_index(inplace=True) # Ensure Date is a column in the DataFrame
    
    rs_rating, comp_rating, eps = getFinancialRatings(hist, financials, balance_sheet, stock_info)
    is_trend_template = isTrendTemplate(data, hist, date_study, b_check_trend_exponential)
    is_vcp_pattern, is_vcp_breakout, price_increase, volume_increase = isVCP(hist)

    kpi_row = {
        "Date": date_study,
        "Close": hist["Close"].iloc[-1],
        "PriceIncrease": price_increase,
        "VolumeIncrease": volume_increase,
        "RS_Rating": rs_rating,
        "Comp_Rating": comp_rating,
        "EPS": eps,
        "isTrendTemplate": is_trend_template,
        "isVcpPattern": is_vcp_pattern,
        "isVcpBreakout": is_vcp_breakout
    }
    return kpi_row

# output: (getKpiAtDay) kpi_row(s)
def getKpiAtPeriod(symbol, start_date, end_date, b_check_trend_exponential):
    kpi_rows = []
    active_dates = determineActiveDates(symbol, start_date, end_date)
    
    for date_study in active_dates:
        print(f"Processing {symbol} at {date_study} EST")

        kpi_row = getKpiAtDay(symbol, date_study, b_check_trend_exponential)
        kpi_rows.append(kpi_row)
    
    kpi_results = pd.DataFrame(kpi_rows)
    return kpi_results

# output: (getKpiAtPeriod) kpi_results + ["isBuyPoint"]
def determineBuyPoints(kpi_results):
    buy_points = []
    buy_points_no_template = []

    prev_row = None
    for index, row in kpi_results.iterrows():
        if prev_row is not None:
            if prev_row["isVcpPattern"] and row["isVcpBreakout"]:
                buy_points_no_template.append(row["Date"])
                if row["isTrendTemplate"]:
                    buy_points.append(row["Date"])
        prev_row = row
    
    kpi_results["isBuyPointNoTemplate"] = kpi_results["Date"].isin(buy_points_no_template)
    kpi_results["isBuyPoint"] = kpi_results["Date"].isin(buy_points)
    return kpi_results

# For Buy and Sell points
def addDatePriceEntries(kpi_results, date_price_entries, ispoint_col, price_col):
    # Initialize columns if not already present
    if ispoint_col not in kpi_results.columns:
        kpi_results[ispoint_col] = False
    if price_col not in kpi_results.columns:
        kpi_results[price_col] = None

    # Update columns
    for date, buy_price in date_price_entries:
        kpi_results.loc[kpi_results["Date"] == date, ispoint_col] = True
        kpi_results.loc[kpi_results["Date"] == date, price_col] = buy_price

# output: (determineBuyPoints) kpi_results +
#        ["isBuyPointActual", "BuyPrice", "isSellPointWhole", "SellPrice1.00",
#         "isSellPointPartial1", "SellPrice0.67", "isSellPointPartial2", "SellPrice0.33"]
def determineSellPoints(kpi_results, r): # r(isk)
    actual_buy_points = []
    whole_sell_points = []
    partial_sell_points_1 = []
    partial_sell_points_2 = []

    is_bought, is_partially_sold = False, False
    for index, row in kpi_results.iterrows():
        date, close = row["Date"], row["Close"]
        if not is_bought:
            if row["isBuyPoint"]:
                buy_price = close
                actual_buy_points.append((date, buy_price))
                
                stop_price = buy_price * (1 - r) # Loss (-r)
                limit_price = buy_price * (1 + 3*r) # Profit (3r)

                is_bought = True
        else:
            # sell below
            if close <= stop_price:
                if not is_partially_sold:
                    whole_sell_points.append((date, stop_price * 1)) # Loss (-r)
                else:
                    partial_sell_points_2.append((date, stop_price * 1/3)) # 2nd 'Loss' (1.5r * 1/3 = 0.5r)

                is_bought, is_partially_sold = False, False

            # sell above
            if close >= limit_price:
                if not is_partially_sold:
                    partial_sell_points_1.append((date, limit_price * 2/3)) # Profit (3r * 2/3 = 2r)
                    # buy_price stays the same
                    stop_price = buy_price * (1 + 1.5*r) # 2nd 'Loss' (1.5r * 1/3 = 0.5r)
                    limit_price = buy_price * (1 + 4.5*r) # 2nd Profit (4.5r * 1/3 = 1.5r)

                    is_partially_sold = True
                else:
                    partial_sell_points_2.append((date, limit_price * 1/3)) # 2nd Profit (4.5r * 1/3 = 1.5r)

                    is_bought, is_partially_sold = False, False

    addDatePriceEntries(kpi_results, actual_buy_points, "isBuyPointActual", "BuyPrice")
    addDatePriceEntries(kpi_results, whole_sell_points, "isSellPointWhole", "SellPrice1.00")
    addDatePriceEntries(kpi_results, partial_sell_points_1, "isSellPointPartial1", "SellPrice0.67")
    addDatePriceEntries(kpi_results, partial_sell_points_2, "isSellPointPartial2", "SellPrice0.33")
    return kpi_results

def addStockTransactions(symbol, kpi_results, r): # r(isk)
    transactions = []
    viable_entries = kpi_results[(kpi_results["isBuyPointActual"] | kpi_results["isSellPointWhole"] |
                                   kpi_results["isSellPointPartial1"] | kpi_results["isSellPointPartial2"])]
    
    for index in range(len(viable_entries)):
        row = viable_entries.iloc[index]
        if row["isBuyPointActual"]:
            buy_price = row["BuyPrice"]
            buy_date = row["Date"]

            sell_price = -1

            try:
                next_row = viable_entries.iloc[index + 1]
                if next_row["isSellPointWhole"]:
                    sell_price = next_row["SellPrice1.00"]
                    sell_date = next_row["Date"]
                else:
                    second_next_row = viable_entries.iloc[index + 2]
                    if next_row["isSellPointPartial1"] and second_next_row["isSellPointPartial2"]:
                        sell_price = next_row["SellPrice0.67"] + second_next_row["SellPrice0.33"]
                        sell_date = second_next_row["Date"]
            except:
                print("index=", index-1, ", len=", len(viable_entries))

            if sell_price != -1:
                profit_percent = (sell_price / buy_price) - 1
                profit_r = profit_percent / r
                tax_percent = profit_percent * (25/100)

                transaction_row = {
                    "Symbol": symbol,
                    "Buy_Date": buy_date,
                    "Sell_Date": sell_date,
                    "Profit[%]": profit_percent * 100,
                    "Profit_r": profit_r,
                    "Tax[%]": tax_percent * 100
                }
                transactions.append(transaction_row)

    return transactions

"""
def summarizeStockActivity(transactions):
    profit_entries = [entry for entry in transactions if entry[0] > 0]
    successful_transactions_percent = len(profit_entries) / len(transactions) * 100
    
    mean_profit_r = sum(entry[1] for entry in profit_entries) / len(profit_entries)

    total_buy_price = sum(entry[1] for entry in profit_entries) / len(profit_entries)

    summary = {
        "Symbol": symbol,
        "Success_Rate[%]": successful_transactions_percent,
        "Success_Mean_r": mean_profit_r,
        "Final_Profit[%]":
    }
    return summary
"""

def main(stocklist, r, num_days_back, tz, b_check_trend_exponential):
    if not stocklist:
        stocklist = readStockList()
    if not createOutputFolder():
        return

    _today = getLastCloseDate(tz)
    start_date = _today - timedelta(days=num_days_back+1) # +1 for isVcpPattern of oldest entry
    end_date = _today

    #start_date = datetime.datetime(year=2024, month=1, day=18)

    transactions = []
    for symbol in stocklist:
        kpi_results = getKpiAtPeriod(symbol, start_date, end_date, b_check_trend_exponential)
        kpi_results = determineBuyPoints(kpi_results)
        kpi_results = determineSellPoints(kpi_results, r)
        printToExcel(symbol, kpi_results)

        transactions.extend(addStockTransactions(symbol, kpi_results, r))
    
    transactions = pd.DataFrame(transactions)
    printToExcel("zzTransactions", transactions)

    #summarizeStockActivity()

# Define the stock list and date for the study
stocklist = []
#stocklist = ["AAPL","HEI","HIMS","WMT","ELAN","EMR","TRI","MKL","QTWO","TMDX","PINS","TGT","USFD","AMZN","META"]
r = 5/100
num_days_back = 365
tz = "Asia/Jerusalem"
b_check_trend_exponential = True

main(stocklist, r, num_days_back, tz, b_check_trend_exponential)
