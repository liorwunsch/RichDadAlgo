function [stock_symbols, stock_buy_prices] = ParseStockList(input_path)
%%
fid = fopen(input_path, 'rt');
text_ = textscan(fid, '%s', 'Delimiter', '\n', 'CollectOutput', true, 'WhiteSpace', '');
fclose(fid);

text_ = text_{1};

stock_symbols = string(text_);
len = length(stock_symbols);

stock_buy_prices = -ones(len, 1);

if contains(stock_symbols(1), ';')
    for i = 1 : len
        split_str = split(stock_symbols(i), ';');
        stock_symbols(i) = strtrim(split_str(1));
        stock_buy_prices(i) = strtrim(split_str(2));
    end
end

stock_symbols = unique(stock_symbols);

end
