function [] = RichDadAlgo(input_path, output_path, days_num, b_visible)
%%
addpath('Utils');

if isfolder(output_path), rmdir(output_path, 's'), end
mkdir(output_path);

%% stocks_data(i) . [ stock_symbol , profit_perc , profit_val , profit_data = [buy_strategy, sell_strategy] , profit_str , b_buy_today]
[stock_symbols] = ParseStockList(fullfile(input_path, 'stocks.txt'));

len = length(stock_symbols);
stocks_data(1, len) = struct;

if len == 0
    return;
end

today = datetime('now', 'Format', 'dd-MM-yyyy');
init_date = today - days_num;

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

max_profit_log_path = fullfile(output_path, 'max_profit.log');
fid = fopen(max_profit_log_path, 'wt');
for i = 1 : len
    fprintf(fid, newline);
    fprintf(fid, '%s', string(stocks_data(i).profit_str));
end
fclose(fid);

% load(fullfile(output_path, 'stocks_data.mat'), 'stocks_data');

str = [newline, 'Stocks (', char(init_date), ' to ', char(today), ')'];
for i = 1 : len
    str = [str, newline, num2str(i), '. ']; %#ok
    if i < 10
        str = [str, ' ']; %#ok
    end
    str = [str, char(stocks_data(i).stock_symbol), ' ']; %#ok
    str = [str, char(9), '(', num2str(stocks_data(i).profit_perc, '%.2f'), '%) ']; %#ok
end
disp(str);

%%
str = [newline, 'Buy Today: ', newline];
for i = 1 : len
    if stocks_data(i).b_buy_today
        if stocks_data(i).profit_perc > 1
            str = [str, char(stocks_data(i).stock_symbol), ', ']; %#ok
        end
    end
end
str = [str(1:end-2), newline];
disp(str);

%%
stock_symbols = [stocks_data.stock_symbol]';
[active_stock_symbols, active_stock_buy_prices] = ParseStockList(fullfile(input_path, 'stocks_active.txt'));
str = newline;
for i = 1 : length(active_stock_symbols)
    k = find(stock_symbols == active_stock_symbols(i), 1);
    if isempty(k)
        warning([char(active_stock_symbols(i)), ' not found in data']);
        continue;
    end
    str = [str, char(stocks_data(k).stock_symbol)]; %#ok
    str = [str, ', ', char(9), 'bought at ', num2str(active_stock_buy_prices(i), '%.2f'), '$']; %#ok
    str = [str, ', ', char(9), 'now at ', num2str(stocks_data(k).price_today, '%.2f'), '$']; %#ok
    str = [str, ', ', char(9), 'profit = ', num2str(100 * stocks_data(k).price_today / active_stock_buy_prices(i), '%.2f'), '%']; %#ok
    if stocks_data(k).b_sell_today
        str = [str, ' !! SELL TODAY !!']; %#ok
    end
    str = [str, newline]; %#ok
end
disp(str);

%%
save(fullfile(output_path, 'stocks_data.mat'), 'stocks_data', '-v7.3');

end
