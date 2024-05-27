function [avg_20_vec, avg_70_vec, avg_150_vec] = CalcMovingAvgsData(avg_20_vec, avg_70_vec, avg_150_vec)
%% avg_x_vec(:,i) = [close_price ; 1 if uptrend ]
% avg_x_vec(1,i) = [close_price]

[avg_20_vec(2,:)] = DetermineUptrend(avg_20_vec);
[avg_70_vec(2,:)] = DetermineUptrend(avg_70_vec);
[avg_150_vec(2,:)] = DetermineUptrend(avg_150_vec);

%%
% ylim_ = ylim;
% ylim_ = ylim_(1);
%
% hold on;
% plot(date_vec, ylim_ + 1 + avg_20_vec(2,:), 'DisplayName', 'MA 20 uptrend', 'Color', [0.85 0.325 0.098], 'LineWidth', 1);
% plot(date_vec, ylim_ + 3 + avg_70_vec(2,:), 'DisplayName', 'MA 70 uptrend', 'Color', [0.466 0.674 0.188], 'LineWidth', 1);
% if ~isempty(who('b_show_avg150')) && b_show_avg150
%     plot(date_vec, ylim_ + 5 + avg_150_vec(2,:), 'DisplayName', 'MA 150 uptrend', 'Color', [0.494 0.184 0.556], 'LineWidth', 1);
% end
% hold off;

end
