function [] = RichDadAlgo(input_path, output_path, days_num, b_visible)
%%
addpath('Utils');

if isfolder(output_path), rmdir(output_path, 's'), end
mkdir(output_path);

%% stocks_data(i) . [ stock_symbol , profit_perc , profit_val , profit_data = [buy_strategy, sell_strategy] , profit_str , b_buy_today]
[stock_symbols] = ParseStockList(fullfile(input_path, 'stocks.txt'));

if isempty(stock_symbols)
    return;
end

%%
today = datetime('now', 'Format', 'dd-MM-yyyy');
init_date = today - days_num;

len = length(stock_symbols);
stocks_data(1, len) = struct;

for i = 1 : len
    stock_symbol = stock_symbols(i);
    [profit_data, profit_str, b_buy_today, b_sell_today, price_today] = StockCharts(stock_symbol, init_date, b_visible, output_path);

    stocks_data(i).stock_symbol = stock_symbol;
    stocks_data(i).profit_perc = profit_data(1);
    stocks_data(i).profit_val = profit_data(2);
    stocks_data(i).profit_data = profit_data(3:4);
    stocks_data(i).profit_str = profit_str;
    stocks_data(i).b_buy_today = b_buy_today;
    stocks_data(i).b_sell_today = b_sell_today;
    stocks_data(i).price_today = price_today;
end

%%
[profit_percs] = [stocks_data.profit_perc];

[~, idx] = sort(profit_percs, 'descend');
stocks_data = stocks_data(idx);

save(fullfile(output_path, 'stocks_data.mat'), 'stocks_data', '-v7.3');

%%
% output_path = 'Output';
% load(fullfile(output_path, 'stocks_data.mat'), 'stocks_data');

PrintStockProfits(output_path, init_date, today, stocks_data)
PrintBuyTodayAlerts(stocks_data);
PrintActiveStocksData(input_path, stocks_data);

end
