function [buy_vec, last_buy_i] = DetermineBuy(avg_20_vec, avg_70_vec, buy_strategy)
%% buy_vec . [ buy(i) = [true if buy] , reason(i) = [string] ]
% avg_x_vec(:,i) = [close_price ; 1 if uptrend ]
% strategy 1: uptrend 20 cross uptrend 70
% strategy 2: strategy 1 + downtrend 70 changes to uptrend 70 (while uptrend 20 above it)

len = size(avg_20_vec, 2);
buy_vec.buy = false(1, len);
buy_vec.reason = strings(1, len);

last_buy_i = 0;
prev_20 = avg_20_vec(1,1);
prev_70 = avg_70_vec(1,1);
for i = 2 : len
    curr_20 = avg_20_vec(1,i);
    curr_70 = avg_70_vec(1,i);

    uptrend_20 = avg_20_vec(2,i);
    uptrend_70 = avg_70_vec(2,i);

    if ~isnan(uptrend_20) && ~isnan(uptrend_70)
        if buy_strategy >= 1
            if uptrend_20 && uptrend_70 && (~isnan(avg_70_vec(2,i-1)) && avg_70_vec(2,i-1)) && (prev_20 <= prev_70 && curr_20 > curr_70)
                buy_vec.buy(i) = true;
                buy_vec.reason(i) = "uptrend 20 cross uptrend 70";
            end
        end

        if ~isnan(avg_70_vec(2,i-1)) && (buy_strategy >= 2 && ~buy_vec.buy(i))
            if uptrend_20 && (~avg_70_vec(2,i-1) && uptrend_70) && curr_20 > curr_70
                buy_vec.buy(i) = true;
                buy_vec.reason(i) = "downtrend 70 changes to uptrend 70 (while uptrend 20 above it)";
            end
        end
    end

    if buy_vec.buy(i)
        last_buy_i = i;
    end

    prev_20 = curr_20;
    prev_70 = curr_70;
end

% if sum(buy_vec.buy == true) == 0
%     buy_vec.buy(1) = true;
%     buy_vec.reason(1) = 'no buying points';
% end

%%
% hold on;
% for i = 1 : len
%     if buy_vec.buy(i)
%         xline(date_vec(i), 'Color', 'b', 'DisplayName', 'buy');
%     end
% end
% hold off;

end
