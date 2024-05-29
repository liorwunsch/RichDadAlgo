function [] = PrintBuyTodayAlerts(stocks_data)
%% stocks_data(i) . [ stock_symbol , profit_perc , profit_val , profit_data = [buy_strategy, sell_strategy] , profit_str , b_buy_today]

len = length(stocks_data);

str = [newline, 'Buy Today: ', newline];

for i = 1 : len
    if stocks_data(i).b_buy_today
        str = [str, char(stocks_data(i).stock_symbol), ', ']; %#ok
        str = [str, num2str(stocks_data(i).profit_perc, '%.2f'), '%']; %#ok
        str = [str, newline]; %#ok
    end
end

disp(str);

end
