function [max_profit_data, max_profit_str, b_buy_today] = StockCharts(stock_symbol, init_date, b_visible, output_path)
%% one stock chart as input
[data_] = ParseStockData(stock_symbol, init_date);

[date_vec, price_vec, avg_20_vec, avg_70_vec, avg_150_vec] = CalcMovingAvgs(data_);
[fig_path] = PlotMovingAvgs(stock_symbol, date_vec, price_vec, avg_20_vec, avg_70_vec, avg_150_vec, b_visible, output_path);

[avg_20_vec, avg_70_vec, ~] = CalcMovingAvgsData(avg_20_vec, avg_70_vec, avg_150_vec);

%%
for strategy_ind = 1:2
    [buy_vec, last_buy_i] = DetermineBuy(avg_20_vec, avg_70_vec, strategy_ind);
    [sell_vec, last_sell_i] = DetermineSell(avg_20_vec, avg_70_vec, strategy_ind, buy_vec);

    % if there are no sell points after last buy point, add a sell point at last
    if last_buy_i ~= 0 && last_sell_i < last_buy_i
        sell_vec.sell(end) = true;
        sell_vec.reason(end) = "no sell points";
    end

    buy_struct(strategy_ind).buy_vec = buy_vec; %#ok
    sell_struct(strategy_ind).sell_vec = sell_vec; %#ok
end

save_path = fullfile(output_path, 'Detailed', stock_symbol);
if isfolder(save_path), rmdir(save_path, 's'), end
mkdir(save_path);
diary(fullfile(save_path, [char(stock_symbol), '.log']));

max_profit_data = -101 .* ones(1, 4); % [percent, usd, buy_strategy, sell_strategy]
max_profit_str = "";
for buy_strategy = 1%:2
    for sell_strategy = 1%:2
        fig = open([char(fig_path), '.fig']);
        output_name = [num2str(buy_strategy), '_', num2str(sell_strategy)];

        [net_profit, net_earnings, profit_vec, str] = CalcProfit(date_vec, price_vec, buy_struct(buy_strategy).buy_vec, sell_struct(sell_strategy).sell_vec);
        str = [newline, char(stock_symbol), ' ', output_name, str]; %#ok
        disp(str);

        profit_data = [net_profit, net_earnings, buy_strategy, sell_strategy];
        PlotProfitPoints(profit_data, profit_vec);

        set(gcf, 'InvertHardcopy', 'off');
        saveas(fig, fullfile(save_path, [char(stock_symbol), '_', output_name, '.png']));
        saveas(fig, fullfile(save_path, [char(stock_symbol), '_', output_name, '.fig']));

        if net_profit > max_profit_data(1)
            max_profit_data = profit_data;
            max_profit_fig = fig;
            max_profit_str = str;
        end
    end
end

diary off;

%%
if ~isempty(who('max_profit_fig'))
    set(gcf, 'InvertHardcopy', 'off');
    saveas(max_profit_fig, [char(fig_path), '.png']);
else
    fig = open([char(fig_path), '.fig']);
    set(gcf, 'InvertHardcopy', 'off');
    saveas(fig, [char(fig_path), '.png']);
end

delete([char(fig_path), '.fig']);

%% buy_vec . [ buy(i) = [true if buy] , reason(i) = [string] ]
b_buy_today = false;
if ~isempty(who('max_profit_fig'))
    max_profit_buy_vec = buy_struct(max_profit_data(3)).buy_vec;
    if max_profit_buy_vec.buy(end)
        b_buy_today = true;
    end
end

close all;

end
