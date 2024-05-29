function [] = PrintActiveStocksData(input_path, stocks_data)
%% stocks_data(i) . [ stock_symbol , profit_perc , profit_val , profit_data = [buy_strategy, sell_strategy] , profit_str , b_buy_today]

stock_symbols = [stocks_data.stock_symbol]';

[active_stock_symbols, active_stock_buy_prices, active_stock_buy_dates] = ParseStockList(fullfile(input_path, 'stocks_active.txt'));
if isempty(active_stock_buy_prices)
    return;
end

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
    str = [str, ',  ', char(9), 'profit = ', num2str(100 * (stocks_data(k).price_today - active_stock_buy_prices(i)) / active_stock_buy_prices(i), '%.2f'), '%']; %#ok
    
    if stocks_data(k).b_sell_today
        str = [str, ' !! SELL TODAY !!']; %#ok
    end
    
    str = [str, newline]; %#ok
end

disp(str);

end
