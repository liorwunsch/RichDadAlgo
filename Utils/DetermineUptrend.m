function [uptrend_vec] = DetermineUptrend(price_vec)
%% uptrend_vec(i) = [1 if uptrend]
% price_vec(i) = [close_price]

len = length(price_vec);
uptrend_vec = NaN(1, len);

prev = price_vec(1);
for i = 2 : len
    curr = price_vec(i);

    if ~isnan(prev) && ~isnan(curr)
        uptrend_vec(i) = (curr >= prev);
    end
    
    prev = curr;
end

end
