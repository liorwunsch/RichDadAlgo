function [] = PrintStockProfits(output_path, init_date, today, stocks_data)
%% stocks_data(i) . [ stock_symbol , profit_perc , profit_val , profit_data = [buy_strategy, sell_strategy] , profit_str , b_buy_today]

len = length(stocks_data);

max_profit_log_path = fullfile(output_path, 'max_profit.log');

fid = fopen(max_profit_log_path, 'wt');
for i = 1 : len
    fprintf(fid, newline);
    fprintf(fid, '%s', string(stocks_data(i).profit_str));
end
fclose(fid);

%%
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

end
