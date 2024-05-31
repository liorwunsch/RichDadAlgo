# RichDadAlgo

## Overview
RichDadAlgo is a Python-based tool for calculating the profit of investing in stocks using a strategy based on the Simple Moving Averages (SMA) - specifically, the 20-day and 70-day SMAs.

## Features
- Fetches historical stock data
- Calculates 20-day and 70-day SMAs
- Executes trading strategy based on SMA crossovers
- Computes profit/loss from the trading strategy
- Suggests to buy or sell a stock

Happy trading! 🚀📈

<sub>I'm not a financial advisor and can't be held responsible for any actions you take based on my advice.</sub>


# Yahoo Finance Fetcher

This project fetches stock data from Yahoo Finance using `libcurl` and parses the JSON response using `nlohmann/json`.

## Installation Instructions

### On Windows

#### Install libcurl:

1. Download a prebuilt libcurl binary from [curl.se](https://curl.se/download.html).
2. Extract the files and place them in a directory (e.g., `C:\Users\User\curl-8.8.0`).
3. Add the `include` and `lib` directories to `Configuration Properties\C/C++\General\Additional Include Directories`.
4. Add the `lib` directory to `Configuration Properties\Linker\General\Additional Library Directories`.
5. Add `libcurl.lib` to the `Configuration Properties\Linker\Input\Additional Dependencies`.

#### Install nlohmann/json:

1. Download the single-header file `json.hpp` from [nlohmann/json releases](https://github.com/nlohmann/json/blob/develop/single_include/nlohmann/json.hpp).
2. Place the `json.hpp` file in your project's include directory.
3. Add your `include` folder to `Configuration Properties\C/C++\General\Additional Include Directories`.
