import yfinance as yf
import pandas as pd 
import numpy as np
import datetime
from datetime import timedelta
import time 
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
import os
import shutil

# Save to Excel with the first row and first column frozen, adjusted column widths, and defined as a table
def printToExcel(file_name, results=pd.DataFrame()):
    if results.empty:
        print("printToExcel: " + file_name + "'s results is empty")
        return
    output_filename = f"Output/{file_name}.xlsx"
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
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

# Cumulative performance over the last `n` quarters
def calcQuarterPerformance(closes, n):
    length = min(len(closes), n * int(252 / 4)) # Calculate the number of trading days to consider, assuming 252 trading days per year
    prices = closes.tail(length)                # Get the closing prices for the last `length` days
    pct_chg = prices.pct_change().dropna()      # Compute the daily percentage changes in closing prices
    perf_cum = (pct_chg + 1).cumprod() - 1      # Calculate the cumulative performance

    quarter_performance = perf_cum.tail(1).item()              # Return the cumulative performance of the last day in this period
    return quarter_performance

# Relative Strength (RS) Rating
def calcRsRating(data):
    closes = data["Close"].iloc[-252:]
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

def getFinancialRatings(data, financials, balance_sheet, stock_info):
    rs_rating = calcRsRating(data)
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

def isTrendTemplate(data):
    current_close = data["Close"].iloc[-1] # -1 is for the last value

    ma_20, ma_50, ma_70, ma_150, ma_200, ma_200_20 = calcCurrentMovingAverages(data)
    
    low_of_52week = min(data["Close"].iloc[-252:])
    high_of_52week = max(data["Close"].iloc[-252:])

    # Condition checks for stock selection
    condition_1_1 = current_close > ma_150                   # Price > 150-day (30-week) MA
    condition_1_2 = current_close > ma_200                   # Price > 200-day (40-week) MA
    condition_2   = ma_150 > ma_200                         # 150-day MA > 200-day MA
    condition_3   = ma_200 > ma_200_20                      # 200-day MA trending up for at least 1 month (22 days)
    condition_4_1 = ma_50 > ma_150                          # 50-day MA > 150-day MA
    condition_4_2 = ma_50 > ma_200                          # 50-day MA > 200-day MA
    condition_5   = current_close > ma_50                    # Price above 50-day MA
    condition_6   = current_close >= (1.25 * low_of_52week)  # Price at least 25% above 52-week low
    condition_7   = current_close >= (0.75 * high_of_52week) # Price within 25% of 52-week high

    is_trend_template = all([condition_1_1, condition_1_2, condition_2, condition_3, condition_4_1, condition_4_2, condition_5, condition_6, condition_7])
    return is_trend_template

def isVCP(data, _window=5, volume_increase=2, price_increase=1.1):
    # Ensure Date is a column in the DataFrame
    data.reset_index(inplace=True)

    # Calculate moving averages for price and volume
    data["MA_Price"] = data["Close"].rolling(window=_window).mean()
    data["MA_Volume"] = data["Volume"].rolling(window=_window).mean()
    
    # Detect periods of relatively low volatility (price stable around MA_Price)
    data["Volatility"] = np.abs(data["Close"] - data["MA_Price"]) / data["MA_Price"]
    data["Volatility<0.075"] = data["Volatility"] < 0.075
    
    # Detect significant volume increase
    data["Volume_Increase"] = data["Volume"] / data["MA_Volume"]
    data["Volume_Increase>" + str(volume_increase)] = data["Volume_Increase"] > volume_increase
    
    # Detect significant price increase
    data["Price_Increase"] = data["Close"] / data["Close"].shift(1)
    data["Price_Increase>" + str(price_increase)] = data["Price_Increase"] > price_increase
    
    # Combine conditions to detect pre-burst (vcp) pattern
    data["Pre_Burst_Pattern"] = data["Volatility<0.075"]
    data["Breakout"] = data["Price_Increase>" + str(price_increase)] & data["Volume_Increase>" + str(volume_increase)]

    is_vcp_pattern = data["Pre_Burst_Pattern"].iloc[-1]
    is_vcp_breakout = data["Breakout"].iloc[-1]
    return is_vcp_pattern, is_vcp_breakout

def getKpiAtDay(symbol, date_study):
    one_year_ago = date_study - timedelta(days=365)
    data = yf.Ticker(symbol)
    
    financials = data.financials
    balance_sheet = data.balance_sheet
    stock_info = data.info
    data = data.history(start=one_year_ago, end=date_study)
    
    time.sleep(0.01)  # Pause to avoid hitting API limits
    data.reset_index(inplace=True) # Ensure Date is a column in the DataFrame
    
    rs_rating, comp_rating, eps = getFinancialRatings(data, financials, balance_sheet, stock_info)
    is_trend_template = isTrendTemplate(data)
    is_vcp_pattern, is_vcp_breakout = isVCP(data)

    kpi_row = {
        "Date": date_study,
        "Close": data["Close"].iloc[-1],
        "RS_Rating": rs_rating,
        "Comp_Rating": comp_rating,
        "EPS": eps,
        "isTrendTemplate": is_trend_template,
        "isVcpPattern": is_vcp_pattern,
        "isVcpBreakout": is_vcp_breakout
    }
    return kpi_row

# output: (getKpiAtDay) kpi_row(s)
def getKpiAtPeriod(symbol, start_date, end_date):
    kpi_rows = []
    
    date_study = start_date
    while date_study <= end_date:
        print(f"Processing {symbol} at {date_study}")

        kpi_row = getKpiAtDay(symbol, date_study)
        kpi_rows.append(kpi_row)

        date_study += timedelta(days=1)
    
    kpi_results = pd.DataFrame(kpi_rows)
    return kpi_results

# output: (getKpiAtPeriod) kpi_results + ["isBuyPoint"]
def determineBuyPoints(kpi_results):
    buy_points = []

    prev_row = None
    for index, row in kpi_results.iterrows():
        if prev_row is not None:
            if row["isTrendTemplate"] and prev_row["isVcpPattern"] and row["isVcpBreakout"]:
                buy_points.append(row["Date"])
        prev_row = row
    
    kpi_results["isBuyPoint"] = kpi_results["Date"].isin(buy_points)
    return kpi_results

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

def calculateProfitPerTransaction(kpi_results, r): # r(isk)
    transactions = []
    viable_entries = kpi_results[(kpi_results["isBuyPointActual"] | kpi_results["isSellPointWhole"] |
                                   kpi_results["isSellPointPartial1"] | kpi_results["isSellPointPartial2"])]
    
    for index, row in viable_entries.iterrows():
        if row["isBuyPointActual"]:
            buy_price = row["BuyPrice"]
            sell_price = -1

            if index + 1 < len(viable_entries): # last entry or before
                next_row = viable_entries.iloc[index + 1]
                if next_row["isSellPointWhole"]:
                    sell_price = next_row["SellPrice1.00"]

            if sell_price == -1 and index + 2 < len(viable_entries): # two last entries or before
                next_row = viable_entries.iloc[index + 1]
                second_next_row = viable_entries.iloc[index + 2]
                if next_row["isSellPointPartial1"] and second_next_row["isSellPointPartial2"]:
                    sell_price = next_row["SellPrice0.67"] + second_next_row["SellPrice0.33"]

            if sell_price != -1:
                profit_percent = (sell_price / buy_price)
                profit_r = profit_percent / r
                transactions.append((profit_percent, profit_r, buy_price, sell_price))

    return transactions

def summarizeKpiResults(symbol, kpi_results, r): # r(isk)
    transactions = calculateProfitPerTransaction(kpi_results, r)
    
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

def main(stocklist, r):
    folder_name = "Output"
    try:
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        os.makedirs(folder_name)
    except:
        print("CANNOT OPEN FOLDER: ", folder_name)
        return

    _today = datetime.datetime.now()
    if _today.hour < 23 or (_today.hour == 23 and _today.minute < 1): # Israel Time After Hours
        yesterday_ = _today - timedelta(days=1)
        _today = datetime.datetime(yesterday_.year, yesterday_.month, yesterday_.day, 23, 1)
    else:
        _today = datetime.datetime(_today.year, _today.month, _today.day, 23, 1)

    one_year_ago = _today - timedelta(days=30) # 365 - LIOR TO-DO

    for symbol in stocklist:
        kpi_results = getKpiAtPeriod(symbol, one_year_ago, _today)
        kpi_results = determineBuyPoints(kpi_results)
        kpi_results = determineSellPoints(kpi_results, r)
        printToExcel(symbol, kpi_results)

        summary = summarizeKpiResults(symbol, kpi_results, r)

# Define the stock list and date for the study
#stocklist = ["AAPL", "MSFT", "GOOGL", "TMDX", "HIMS", "SNX", "STEP", "AMG", "ANET", "ASR", "EURN", "GBDC", "HASI", "MAIN", "NVO", "OLED", "SPG", "UE", "UTHR", "VRTX", "WPM"]
stocklist = ["HIMS"]
r = 5/100

main(stocklist, r)
