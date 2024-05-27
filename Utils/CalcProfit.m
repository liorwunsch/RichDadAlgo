function [total_net_profit, net_earnings, profit_vec, str] = CalcProfit(date_vec, price_vec, buy_vec, sell_vec)
%% one strategy as input
% total_net_profit (%) - over all time considering price_invested, gross_earnings and taxes
% profit_vec . [ profit(i) , buy_price(i) , buy_date(i) , buy_reason(i) , sell_price(i) , sell_date(i) , sell_reason(i) ]
% date_vec(i) = [date]
% price_vec(1,i) = [close_price]
% buy_vec . [ buy(i) = [true if buy] , reason(i) = [string] ]
% sell_vec . [ sell(i) = [true if sell] , reason(i) = [string] ]

sell_ind = 1;
b_waiting_to_sell = false;

len = length(price_vec);
for i = 1 : len
    if ~b_waiting_to_sell && buy_vec.buy(i)
        buy_price = price_vec(i);
        buy_date = date_vec(i);
        buy_reason = buy_vec.reason(i);
        b_waiting_to_sell = true;
        continue;
    end
    if b_waiting_to_sell && sell_vec.sell(i)
        sell_price = price_vec(i);
        sell_date = date_vec(i);
        sell_reason = sell_vec.reason(i);
        b_waiting_to_sell = false;

        profit_vec.profit(sell_ind) = ((sell_price - buy_price) / buy_price) * 100;
        profit_vec.buy_price(sell_ind) = buy_price;
        profit_vec.buy_date(sell_ind) = buy_date;
        profit_vec.buy_reason(sell_ind) = buy_reason;
        profit_vec.sell_price(sell_ind) = sell_price;
        profit_vec.sell_date(sell_ind) = sell_date;
        profit_vec.sell_reason(sell_ind) = sell_reason;
        sell_ind = sell_ind + 1;
    end
end

%%
if isempty(who('profit_vec'))
    profit_vec = [];
    p_len = 0;
else
    p_len = length(profit_vec.profit);
end

b_profit = false(1, p_len);
price_invested = 0; % how much money invested
gross_earnings = 0; % earnings including profits and losses from transactions
taxes = 0; % taxes including tax-debts from profits and tax-shields from losses

str = [];
for i = 1 : p_len
    str = [str, newline, 'bought: ', char(profit_vec.buy_date(i)), ' (', num2str(profit_vec.buy_price(i), '%.2f'), '$)']; %#ok
    str = [str, char(9), ', sold: ', char(profit_vec.sell_date(i)), ' (', num2str(profit_vec.sell_price(i), '%.2f'), '$)']; %#ok
    str = [str, char(9), ', gross_profit = ', num2str(profit_vec.profit(i), '%.2f'), '%']; %#ok
    str = [str, '  ', char(9), 'buy: ', char(profit_vec.buy_reason(i)), '.']; %#ok
    str = [str, char(9), 'sell: ', char(profit_vec.sell_reason(i)), '.']; %#ok

    if profit_vec.profit(i) > 0
        b_profit(i) = true;
    end

    price_invested = price_invested + profit_vec.buy_price(i);
    curr_earnings = profit_vec.sell_price(i) - profit_vec.buy_price(i);
    gross_earnings = gross_earnings + curr_earnings;

    % debts mean 25% of profit and shields mean 25% of loss
    % taxes are increased on profit and decreased on loss (curr_earnings < 0)
    if curr_earnings > 0 || (curr_earnings < 0) % && days_num < 7 * 365) % tax-shields apply up to 7 years
        taxes = taxes + 0.25 * curr_earnings;
    end
end

if taxes < 0
    taxes = 0; % tax-shield only applies to taxes, it cannot be considered as profit
end
if gross_earnings >= 0 && taxes > gross_earnings
    taxes = gross_earnings; % it shouldn't come to this, but let's protect against taxes that are above earnings, meaning loss from taxes
end

if p_len ~= 0
    num_of_profit = sum(b_profit == true);
    num_of_loss = p_len - num_of_profit;
    net_earnings = gross_earnings - taxes;
    total_net_profit = 100 * (net_earnings / price_invested);
else
    num_of_profit = 0;
    num_of_loss = 0;
    net_earnings = 0;
    total_net_profit = 0;
    p_len = 1; % to prevent divide by zero
end

str = [str, newline, 'profit_chance = ', num2str((num_of_profit / p_len) * 100, '%.2f'), '%'];
str = [str, ' (', num2str(num_of_profit), ' profits)'];
str = [str, ' (', num2str(num_of_loss), ' losses)'];
str = [str, newline, 'total_net_profit = ', num2str(total_net_profit, '%.2f'), '%'];
str = [str, ' (invested ', num2str(price_invested, '%.2f'), '$, earned ', num2str(net_earnings, '%.2f'), '$)'];

end
