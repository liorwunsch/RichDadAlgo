function [date_vec, price_vec, avg_20_vec, avg_70_vec, avg_150_vec] = CalcMovingAvgs(data_)
%% date_vec(i) = [date]
% price/avg_x_vec(1,i) = [close_price]
% data_ . [ Date , Open , High , Low , Close , AdjClose , Volume ]

len = length(data_);
price_vec = NaN(1, len);
avg_20_vec = price_vec;
avg_70_vec = price_vec;
avg_150_vec = price_vec;

for i = 1 : len
    date_vec(1,i) = data_(i).Date; %#ok
    price_vec(1,i) = data_(i).Close;

    if i >= 20
        x = 20;
        avg_20_vec(i) = mean(price_vec(i-x+1:i));
    end
    if i >= 70
        x = 70;
        avg_70_vec(i) = mean(price_vec(i-x+1:i));
    end
    if i >= 150
        avg_150_vec(i) = mean(price_vec(i-x+1:i));
    end
end

end
