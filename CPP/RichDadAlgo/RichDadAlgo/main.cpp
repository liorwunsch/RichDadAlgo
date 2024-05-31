#include "YahooFinanceFetcher.h"

int main()
{
	YahooFinanceFetcher fetcher;
	ParseDefs::Root data;
	fetcher.fetchData("AAPL", "3mo", data); // validRanges: ["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]

	// Print some fetched data as a demonstration
	for (const auto & result : data.chart.result)
	{
		std::cout << "Symbol: " << result.meta.symbol << std::endl;
		std::cout << "Regular Market Price: " << result.meta.regularMarketPrice << std::endl;
		// Add more data output as needed
	}

	return 0;
}
