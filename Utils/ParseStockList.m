function [stock_symbols, stock_buy_prices, stock_buy_dates] = ParseStockList(input_path)
%%
fid = fopen(input_path, 'rt');
text_ = textscan(fid, '%s', 'Delimiter', '\n', 'CollectOutput', true, 'WhiteSpace', '');
fclose(fid);

text_ = text_{1};

stock_symbols = string(text_);
stock_symbols(startsWith(stock_symbols, '//')) = [];
stock_symbols = strtrim(stock_symbols);

%%
stock_buy_prices = [];

len = length(stock_symbols);
for i = 1 : len
    split_str = split(stock_symbols(i), ';');
    stock_symbols(i) = strtrim(split_str(1));
    if length(split_str) >= 2
        stock_buy_prices(i) = str2double(strtrim(split_str(2))); %#ok
    end
    if length(split_str) >= 3
        stock_buy_dates(i) = datetime(strtrim(split_str(3))); %#ok
    end
end

if isempty(stock_buy_prices)
    stock_buy_dates = [];
end

end
