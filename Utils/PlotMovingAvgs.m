function [fig_path] = PlotMovingAvgs(stock_symbol, date_vec, price_vec, avg_20_vec, avg_70_vec, avg_150_vec, b_visible, save_path, b_show_avg150)
%% date_vec(i) = [date]
% price/avg_x_vec(1,i) = [close_price]

fig = figure('Visible', b_visible, 'Position', [0 0 3840 2160]);
hold on; grid on; grid minor;

ax = gca; ax.GridColor = [1 1 1];
set(gca, 'Color', [40 40 40] / 255);
legend(gca, 'show', 'Location', 'NW', 'Interpreter', 'none', 'Color', 'none', 'TextColor', 'w');

title([stock_symbol, ' (1D)']);
xlabel('Date');
ylabel('Price');
xlim('auto');
ylim('auto');

plot(date_vec, price_vec, 'DisplayName', 'Value', 'Color', [0 0.447 0.741], 'LineWidth', 1);
plot(date_vec, avg_20_vec, 'DisplayName', 'MA 20', 'Color', [0.85 0.325 0.098], 'LineWidth', 1);
plot(date_vec, avg_70_vec, 'DisplayName', 'MA 70', 'Color', [0.466 0.674 0.188], 'LineWidth', 1);
if ~isempty(who('b_show_avg150')) && b_show_avg150
    plot(date_vec, avg_150_vec, 'DisplayName', 'MA 150', 'Color', [0.494 0.184 0.556], 'LineWidth', 1);
end

hold off;

set(gcf, 'InvertHardcopy', 'off');

fig_path = fullfile(save_path, stock_symbol);
saveas(fig, [char(fig_path), '.fig']);
close(fig);

end
