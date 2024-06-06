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
def printToExcel(symbol, results):
    output_filename = f"Output/{symbol}.xlsx"
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
    return perf_cum.tail(1).item()              # Return the cumulative performance of the last day in this period

# Relative Strength (RS) Rating
def calcRsRating(data):
    closes = data["Close"].iloc[-252:]
    try:
        quarters1 = calcQuarterPerformance(closes, 1)
        quarters2 = calcQuarterPerformance(closes, 2)
        quarters3 = calcQuarterPerformance(closes, 3)
        quarters4 = calcQuarterPerformance(closes, 4)
        return (0.4*quarters1 + 0.2*quarters2 + 0.2*quarters3 + 0.2*quarters4) * 100
    except:
        return 0

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
    return 0.25*rs_rating + 0.25*earnings_growth + 0.25*sales_growth + 0.125*profit_margin + 0.125*roe # Normalize and weight the metrics

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

    return all([condition_1_1, condition_1_2, condition_2, condition_3, condition_4_1, condition_4_2, condition_5, condition_6, condition_7])

def shouldIBuyToday(symbol, date_study):
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

    return rs_rating, comp_rating, eps, is_trend_template

def whenShouldIBuy(symbol, start_date, end_date):
    results = pd.DataFrame(columns=["Date", "RS_Rating", "Comp_Rating", "EPS", "isTrendTemplate"])

    date_study = start_date
    rows = []
    while date_study <= end_date:
        print(f"Processing {symbol} at {date_study}")

        rs_rating, comp_rating, eps, is_trend_template = shouldIBuyToday(symbol, date_study)
        new_row = {
            "Date": date_study, 
            "RS_Rating": rs_rating,
            "Comp_Rating": comp_rating,
            "EPS": eps,
            "isTrendTemplate": is_trend_template
        }
        rows.append(new_row)
        date_study += timedelta(days=1)

    results = pd.concat([results, pd.DataFrame(rows)], ignore_index=True)
    printToExcel(symbol, results)

    return results

def main(stocklist):
    folder_name = "Output"
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    os.makedirs(folder_name)
    
    today_ = datetime.datetime.now()
    if today_.hour < 23 or (today_.hour == 23 and today_.minute < 1): # Israel Time After Hours
        yesterday_ = today_ - timedelta(days=1)
        today_ = datetime.datetime(yesterday_.year, yesterday_.month, yesterday_.day, 23, 1)
    else:
        today_ = datetime.datetime(today_.year, today_.month, today_.day, 23, 1)

    one_year_ago = today_ - timedelta(days=2) # 365

    for symbol in stocklist:
        results = whenShouldIBuy(symbol, one_year_ago, today_)

# Define the stock list and date for the study
#stocklist = ["AAPL", "MSFT", "GOOGL", "TMDX", "HIMS", "SNX", "STEP", "AMG", "ANET", "ASR", "EURN", "GBDC", "HASI", "MAIN", "NVO", "OLED", "SPG", "UE", "UTHR", "VRTX", "WPM"]
stocklist = ["HIMS"]

main(stocklist)
