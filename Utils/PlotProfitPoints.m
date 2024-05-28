function [] = PlotProfitPoints(profit_data, profit_vec)
%% max_profit_data = [total_profit, buy_strategy, sell_strategy]
% profit_vec . [ profit(i) , buy_price(i) , buy_date(i) , buy_reason(i) , sell_price(i) , sell_date(i) , sell_reason(i) ]

[total_profit, buy_strategy, sell_strategy] = deal(profit_data(1), profit_data(2), profit_data(3));

hold on;
ylim_ = ylim;

if total_profit ~= 0
    for i = 1 : length(profit_vec.profit)
        buy_price = profit_vec.buy_price(i);
        buy_date = profit_vec.buy_date(i);
        buy_reason = [char(profit_vec.buy_reason(i)), newline, '(', num2str(buy_price), ')'];

        plot(buy_date, buy_price, '-o', 'MarkerSize', 15, 'MarkerEdgeColor', 'g', 'DisplayName', 'buy');
        text(buy_date, ylim_(2) * 0.98, buy_reason, 'Interpreter', 'none', 'HorizontalAlignment', 'Center', 'FontSize', 8, 'Color', 'g');
        plot([buy_date, buy_date], ylim_, '--', 'DisplayName', 'buy', 'Color', 'g');

        sell_price = profit_vec.sell_price(i);
        sell_date = profit_vec.sell_date(i);
        sell_reason = [char(profit_vec.sell_reason(i)), newline, '(', num2str(sell_price), ')'];

        plot(sell_date, sell_price, '-o', 'MarkerSize', 15, 'MarkerEdgeColor', 'r', 'DisplayName', 'sell');
        text(sell_date, ylim_(2) * 0.97, sell_reason, 'Interpreter', 'none', 'HorizontalAlignment', 'Center', 'FontSize', 8, 'Color', 'r');
        plot([sell_date, sell_date], ylim_, '--', 'DisplayName', 'sell', 'Color', 'r');
    end
end

color_ = 'g';
if total_profit < 0
    color_ = 'r';
end

annotation('textbox', [0.2, 0.55, 0.1, 0.1], 'String', ['Profit = ', num2str(total_profit), '%'], 'Interpreter', 'none', 'HorizontalAlignment', 'Center', 'FontSize', 10, 'Color', color_);
annotation('textbox', [0.2, 0.5, 0.1, 0.1], 'String', ['Buy Strategy = ', num2str(buy_strategy)], 'Interpreter', 'none', 'HorizontalAlignment', 'Center', 'FontSize', 10, 'Color', 'g');
annotation('textbox', [0.2, 0.45, 0.1, 0.1], 'String', ['Sell Strategy = ', num2str(sell_strategy)], 'Interpreter', 'none', 'HorizontalAlignment', 'Center', 'FontSize', 10, 'Color', 'r');
hold off;

end
