function [sell_vec, last_sell_i] = DetermineSell(avg_20_vec, avg_70_vec, sell_strategy, buy_vec)
%% sell_vec . [ sell(i) = [true if sell] , reason(i) = [string] ]
% avg_x_vec(:,i) = [close_price ; 1 if uptrend ]
% strategy 1: uptrend 70 changes to downtrend 70 + downtrend 20 cross uptrend 70
% strategy 2: strategy 1 + uptrend 20 cross uptrend 70 (1) days after

len = size(avg_20_vec, 2);
sell_vec.sell = false(1, len);
sell_vec.reason = strings(1, len);

last_sell_i = 0;
prev_20 = avg_20_vec(1,1);
prev_70 = avg_70_vec(1,1);
for i = 2 : len
    curr_20 = avg_20_vec(1,i);
    curr_70 = avg_70_vec(1,i);

    uptrend_20 = avg_20_vec(2,i);
    uptrend_70 = avg_70_vec(2,i);

    if ~isnan(uptrend_20) && ~isnan(uptrend_70)
        if sell_strategy >= 1
            if ~isnan(avg_70_vec(1,i-1)) && avg_70_vec(1,i) <= 0.99 * avg_70_vec(1,i-1)
                sell_vec.sell(i) = true;
                sell_vec.reason(i) = "uptrend 70 changes to downtrend 70";
            end
            if ~uptrend_20 && uptrend_70 && (prev_20 >= prev_70 && curr_20 < curr_70)
                sell_vec.sell(i) = true;
                sell_vec.reason(i) = "downtrend 20 cross uptrend 70";
            end
        end

        if sell_strategy >= 2
            if sell_vec.sell(i) && i < len && buy_vec.buy(i+1)
                sell_vec.sell(i) = false;
                sell_vec.reason(i) = "uptrend 20 cross uptrend 70 (1) days after";
            end
        end
        
        if sell_strategy >= 3
           % TODO - add sell point where stock value drops 5% less than highest value after buy 
        end

        if sell_vec.sell(i)
            last_sell_i = i;
        end
    end

    prev_20 = curr_20;
    prev_70 = curr_70;
end

% if sum(sell_vec.sell == true) == 0
%     sell_vec.sell(end) = true;
%     sell_vec.reason(end) = 'no selling points';
% end

%%
% hold on;
% for i = 1 : len
%     if sell_vec.sell(i)
%         xline(date_vec(i), 'Color', 'r', 'DisplayName', 'sell');
%     end
% end
% hold off;

end
