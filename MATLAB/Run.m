close all;
fclose all;
clear;

diary off;
clc;

dbstop if error;
warning('off', 'MATLAB:table:ModifiedAndSavedVarnames');
warning('off', 'MATLAB:legend:IgnoringExtraEntries');

input_path = '.';
output_path = 'Output';
days_num = 365;
b_visible = 'off';

RichDadAlgo(input_path, output_path, days_num, b_visible);

warning('on', 'MATLAB:table:ModifiedAndSavedVarnames');
warning('on', 'MATLAB:legend:IgnoringExtraEntries');

close all;
fclose all;
clear;
