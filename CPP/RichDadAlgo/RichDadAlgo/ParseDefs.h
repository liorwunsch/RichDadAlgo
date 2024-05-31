#include <iostream>
#include <string>
#include <vector>
#include "json.hpp"

namespace ParseDefs
{
	struct Quote
	{
		std::vector<double> low;
		std::vector<int64_t> volume;
		std::vector<double> open_;
		std::vector<double> high;
		std::vector<double> close;
	};

	struct Indicators
	{
		std::vector<Quote> quote;
	};

	struct Meta
	{
		std::string currency;
		std::string symbol;
		std::string exchangeName;
		std::string fullExchangeName;
		std::string instrumentType;
		int64_t firstTradeDate;
		int64_t regularMarketTime;
		bool hasPrePostMarketData;
		int gmtoffset;
		std::string timezone;
		std::string exchangeTimezoneName;
		double regularMarketPrice;
		double fiftyTwoWeekHigh;
		double fiftyTwoWeekLow;
		double regularMarketDayHigh;
		double regularMarketDayLow;
		int64_t regularMarketVolume;
		double chartPreviousClose;
		int priceHint;
		std::string dataGranularity;
		std::string range;
		std::vector<std::string> validRanges;
	};

	struct Result
	{
		Meta meta;
		std::vector<int64_t> timestamp;
		Indicators indicators;
	};

	struct Chart
	{
		std::vector<Result> result;
	};

	struct Root
	{
		Chart chart;
	};

	void from_json(const nlohmann::json & j, Quote & q)
	{
		j.at("low").get_to(q.low);
		j.at("volume").get_to(q.volume);
		j.at("open").get_to(q.open_);
		j.at("high").get_to(q.high);
		j.at("close").get_to(q.close);
	}

	void from_json(const nlohmann::json & j, Indicators & i)
	{
		j.at("quote").get_to(i.quote);
	}

	void from_json(const nlohmann::json & j, Meta & m)
	{
		j.at("currency").get_to(m.currency);
		j.at("symbol").get_to(m.symbol);
		j.at("exchangeName").get_to(m.exchangeName);
		j.at("fullExchangeName").get_to(m.fullExchangeName);
		j.at("instrumentType").get_to(m.instrumentType);
		j.at("firstTradeDate").get_to(m.firstTradeDate);
		j.at("regularMarketTime").get_to(m.regularMarketTime);
		j.at("hasPrePostMarketData").get_to(m.hasPrePostMarketData);
		j.at("gmtoffset").get_to(m.gmtoffset);
		j.at("timezone").get_to(m.timezone);
		j.at("exchangeTimezoneName").get_to(m.exchangeTimezoneName);
		j.at("regularMarketPrice").get_to(m.regularMarketPrice);
		j.at("fiftyTwoWeekHigh").get_to(m.fiftyTwoWeekHigh);
		j.at("fiftyTwoWeekLow").get_to(m.fiftyTwoWeekLow);
		j.at("regularMarketDayHigh").get_to(m.regularMarketDayHigh);
		j.at("regularMarketDayLow").get_to(m.regularMarketDayLow);
		j.at("regularMarketVolume").get_to(m.regularMarketVolume);
		j.at("chartPreviousClose").get_to(m.chartPreviousClose);
		j.at("priceHint").get_to(m.priceHint);
		j.at("dataGranularity").get_to(m.dataGranularity);
		j.at("range").get_to(m.range);
		j.at("validRanges").get_to(m.validRanges);
	}

	void from_json(const nlohmann::json & j, Result & r)
	{
		j.at("meta").get_to(r.meta);
		j.at("timestamp").get_to(r.timestamp);
		j.at("indicators").get_to(r.indicators);
	}

	void from_json(const nlohmann::json & j, Chart & c)
	{
		j.at("result").get_to(c.result);
	}

	void from_json(const nlohmann::json & j, Root & root)
	{
		j.at("chart").get_to(root.chart);
	}
}
