function [data_] = ParseStockData(stock_symbol, init_date)
%% data_ . [ Date , Open , High , Low , Close , AdjClose , Volume ]

stock_symbol = char(stock_symbol);

[data_] = getMarketDataViaYahoo(stock_symbol, init_date);

data_ = table2struct(data_);

end
