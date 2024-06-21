import sys
import pickle
import yfinance as yf
import pandas as pd 
import numpy as np
import math
import datetime
from datetime import timedelta
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

def createParamsFolder():
    folder_name = "Params"
    try:
        os.makedirs(folder_name)
    except:
        pass
    return True
    
# Save to Excel with the first row and first column frozen, adjusted column widths, and defined as a table
def printToExcel(file_name, results=pd.DataFrame()):
    if results.empty:
        print("printToExcel: " + file_name + "'s results is empty")
        return

    output_filename = f"Output/{file_name}.xlsx"
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        #if "Date" in results.columns:
        #    results['Date'] = results['Date'].dt.tz_localize(None)
        
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

def calcCurrentMovingAverages(hist):
    sma = [20, 50, 70, 150, 200]
    for x in sma:
        hist["SMA_" + str(x)] = hist["Close"].rolling(window=x).mean()
    
    ma_20 = hist["SMA_20"].iloc[-1]
    ma_50 = hist["SMA_50"].iloc[-1]
    ma_70 = hist["SMA_70"].iloc[-1]
    ma_150 = hist["SMA_150"].iloc[-1]
    ma_200 = hist["SMA_200"].iloc[-1]
    ma_200_20 = hist["SMA_200"].iloc[-22]

    return ma_20, ma_50, ma_70, ma_150, ma_200, ma_200_20

# minervini trend template
def isTrendTemplate(hist):
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

# **5** trading days/weeks Back
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
    return is_vcp_pattern

def getKpiAtDay(hist, date_study):
    index = hist.index[hist['Date'] <= date_study].tolist()
    index = index[-1]
    hist = hist.iloc[:index + 1] # +1 for data of today's afterhours and not yesterday's
    hist = hist.copy()

    is_trend_template = isTrendTemplate(hist)
    is_vcp_pattern = isVCP(hist)

    hist_weekly = hist.resample('W', on='Date').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna().reset_index()
    is_vcp_pattern_weekly = isVCP(hist_weekly)

    hist_monthly = hist.resample('ME', on='Date').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna().reset_index()
    is_vcp_pattern_monthly = isVCP(hist_monthly)

    kpi_row = {
        "Date": date_study,
        "isTrendTemplate": is_trend_template,
        "isVcpPattern": is_vcp_pattern,
        "isVcpPattern_Weekly": is_vcp_pattern_weekly,
        "isVcpPattern_Monthly": is_vcp_pattern_monthly
    }
    return kpi_row

# output: (getKpiAtDay) kpi_row(s)
def getKpiAtPeriod(symbol, start_date, end_date):
    pickle_file_path = 'Params/' + symbol + '_kpi_results.pkl'
    if os.path.exists(pickle_file_path):
        with open(pickle_file_path, 'rb') as file:
            kpi_results = pickle.load(file)
            print("Loading " + pickle_file_path)
            return kpi_results

    data = yf.Ticker(symbol)
    hist = data.history(period="max")
    hist = hist.drop_duplicates()
    hist.reset_index(inplace=True) # Ensure Date is a column in the DataFrame

    kpi_rows = []
    active_dates = determineActiveDates(symbol, start_date, end_date)
    
    for date_study in active_dates:
        print(f"Processing {symbol} at {date_study} EST")

        kpi_row = getKpiAtDay(hist, date_study)
        kpi_rows.append(kpi_row)
    
    kpi_results = pd.DataFrame(kpi_rows)
    kpi_results['Date'] = kpi_results['Date'].dt.tz_localize(None)

    prev_row = None
    grouped_kpi_rows = []
    for index, row in kpi_results.iterrows():
        if index == 0:
            date_begin = row['Date']
        else:
            if row['isTrendTemplate'] == prev_row['isTrendTemplate'] and \
                row['isVcpPattern'] == prev_row['isVcpPattern'] and \
                row['isVcpPattern_Weekly'] == prev_row['isVcpPattern_Weekly'] and \
                row['isVcpPattern_Monthly'] == prev_row['isVcpPattern_Monthly']:
                if index == kpi_results.index[-1]:
                    date_end = row['Date']
                    grouped_kpi_row = {
                        "Date_Begin": date_begin,
                        "Date_End": date_end,
                        "isTrendTemplate": row['isTrendTemplate'],
                        "isVcpPattern": row['isVcpPattern'],
                        "isVcpPattern_Weekly": row['isVcpPattern_Weekly'],
                        "isVcpPattern_Monthly": row['isVcpPattern_Monthly']
                    }
                    grouped_kpi_rows.append(grouped_kpi_row)
            else:
                date_end = prev_row['Date']
                grouped_kpi_row = {
                    "Date_Begin": date_begin,
                    "Date_End": date_end,
                    "isTrendTemplate": prev_row['isTrendTemplate'],
                    "isVcpPattern": prev_row['isVcpPattern'],
                    "isVcpPattern_Weekly": prev_row['isVcpPattern_Weekly'],
                    "isVcpPattern_Monthly": prev_row['isVcpPattern_Monthly']
                }
                grouped_kpi_rows.append(grouped_kpi_row)
                date_begin = row['Date']
                if index == kpi_results.index[-1]:
                    date_end = row['Date']
                    grouped_kpi_row = {
                        "Date_Begin": date_begin,
                        "Date_End": date_end,
                        "isTrendTemplate": row['isTrendTemplate'],
                        "isVcpPattern": row['isVcpPattern'],
                        "isVcpPattern_Weekly": row['isVcpPattern_Weekly'],
                        "isVcpPattern_Monthly": row['isVcpPattern_Monthly']
                    }
                    grouped_kpi_rows.append(grouped_kpi_row)
        prev_row = row        
    grouped_kpi_results = pd.DataFrame(grouped_kpi_rows)
    kpi_results = grouped_kpi_results

    indexes = kpi_results.index[kpi_results['isTrendTemplate'] & \
                                    kpi_results['isVcpPattern'] & \
                                    kpi_results['isVcpPattern_Weekly'] & \
                                    kpi_results['isVcpPattern_Monthly']].tolist()
    filtered_kpi_results = kpi_results.iloc[indexes]

    with open(pickle_file_path, 'wb') as file:
        pickle.dump(kpi_results, file)
    printToExcel(symbol, kpi_results)
    printToExcel(symbol + "_Filtered", filtered_kpi_results)
    return kpi_results

def determineDowntrends(symbol, start_date, end_date, is_weekly):
    data = yf.Ticker(symbol)
    hist = data.history(start=start_date, end=end_date+timedelta(days=1)) # +1 for data of today's afterhours and not yesterday's
    hist = hist.drop_duplicates()
    hist.reset_index(inplace=True) # Ensure Date is a column in the DataFrame

    if is_weekly:
        hist = hist.resample('W', on='Date').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna().reset_index()

    downtrend_rows = []
    in_downtrend = False

    prev_row = None
    for index, row in hist.iterrows():
        if prev_row is None:
            prev_row = row
            continue
        if not in_downtrend:
            if row['Close'] < prev_row['Close']:
                in_downtrend = True
                start_date = prev_row['Date'] # peak
                start_close = prev_row['High']
                start_index = index - 1
        else:
            if row['Close'] >= prev_row['Close']:
                in_downtrend = False
                end_index = index - 1
                if end_index > start_index + 1: # ignore downtrend only 1 day
                    end_date = prev_row['Date'] # trough
                    end_close = prev_row['Low']
                    downtrend_row = {
                        "Index": len(downtrend_rows),
                        "Start_Date": start_date,
                        "End_Date": end_date,
                        "High": start_close,
                        "Low": end_close,
                        "Change[%]": 100 * abs((end_close - start_close) / start_close),
                        "Length": end_index - start_index + 1
                    }
                    downtrend_rows.append(downtrend_row)
        prev_row = row

    downtrends = pd.DataFrame(downtrend_rows)
    if not downtrends.empty:
        downtrends['Start_Date'] = downtrends['Start_Date'].dt.tz_localize(None)
        downtrends['End_Date'] = downtrends['End_Date'].dt.tz_localize(None)
    return downtrends

def findSequences(downtrends, index, current_sequence):
    sequences = []
    for i in range(index + 1, len(downtrends)):
        if downtrends['Change[%]'].iloc[i] < downtrends['Change[%]'].iloc[i-1]:
            if downtrends['High'].iloc[i] < downtrends['High'].iloc[i-1]:
                if downtrends['Low'].iloc[i] > downtrends['Low'].iloc[i-1]:
                    new_sequence = current_sequence + [i]
                    sequences.append(new_sequence)
                    sequences += findSequences(downtrends, i, new_sequence)
    return sequences

def determineContractions(downtrends, symbol):
    all_sequences = []
    for i in range(len(downtrends)):
        all_sequences += findSequences(downtrends, i, [i])
    filtered_sequences = [seq for seq in all_sequences if len(seq) > 1]

    contraction_rows = []
    for seq in filtered_sequences:
        contraction_row = {
            "Symbol": symbol,
            "DowntrendIndexes": seq,
            "End_Date": downtrends["End_Date"].iloc[seq[-1]]
        }
        contraction_rows.append(contraction_row)
    contractions = pd.DataFrame(contraction_rows)
    return contractions

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

def main(stocklist, r, num_days_back, tz):
    if not stocklist:
        stocklist = readStockList()
    if not createOutputFolder():
        return
    if not createParamsFolder():
        return

    _today = getLastCloseDate(tz)
    start_date = _today - timedelta(days=num_days_back+1) # +1 for isVcpPattern of oldest entry
    end_date = _today

    #start_date = datetime.datetime(year=2024, month=2, day=1)

    #contractions = []
    #weekly_contractions = []
    for symbol in stocklist:
        kpi_results = getKpiAtPeriod(symbol, start_date, end_date)
        #downtrends = determineDowntrends(symbol, start_date, end_date, False)
        #weekly_downtrends = determineDowntrends(symbol, start_date, end_date, True)
        #printToExcel(symbol + "_Downtrends", downtrends)
        #printToExcel(symbol + "_DowntrendsWeekly", weekly_downtrends)

        #contractions = determineContractions(downtrends, symbol)
        #weekly_contractions = determineContractions(weekly_downtrends, symbol)
        #if not weekly_contractions.empty:
        #    printToExcel(symbol + "_Contractions", contractions)
        #    printToExcel(symbol + "_ContractionsWeekly", weekly_contractions)
        #contractions.extend(determineContractions(downtrends, symbol))
        #weekly_contractions.extend(determineContractions(weekly_downtrends, symbol))

    #contractions = pd.DataFrame(contractions)
    #weekly_contractions = pd.DataFrame(weekly_contractions)

    #printToExcel("zzContractions", contractions)
    #printToExcel("zzContractionsWeekly", weekly_contractions)

# Define the stock list and date for the study
stocklist = ["AAPL","HEI","HIMS","WMT","ELAN","EMR","TRI","MKL","QTWO","TMDX","PINS","TGT","USFD","AMZN","META"] # []
r = 5/100
num_days_back = 365
tz = "Asia/Jerusalem"

main(stocklist, r, num_days_back, tz)
