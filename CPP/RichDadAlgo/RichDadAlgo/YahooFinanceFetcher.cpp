#include "YahooFinanceFetcher.h"
#include <curl/curl.h>

YahooFinanceFetcher::YahooFinanceFetcher()
{
	curl_global_init(CURL_GLOBAL_DEFAULT);
	m_curl_handle = curl_easy_init();
}

YahooFinanceFetcher::~YahooFinanceFetcher()
{
	curl_easy_cleanup(m_curl_handle);
	curl_global_cleanup();
}

void YahooFinanceFetcher::fetchData(const std::string & symbol, const std::string & range, ParseDefs::Root & root)
{
	std::string url =
		"https://query1.finance.yahoo.com/v8/finance/chart/"
		+ symbol
		+ "?range=" + range
		+ "&interval=1d";

	std::string readBuffer;
	curl_easy_setopt(m_curl_handle, CURLOPT_URL, url.c_str());
	curl_easy_setopt(m_curl_handle, CURLOPT_WRITEFUNCTION, WriteCallback);
	curl_easy_setopt(m_curl_handle, CURLOPT_WRITEDATA, &readBuffer);

	CURLcode res = curl_easy_perform(m_curl_handle);

	if (res != CURLE_OK)
	{
		std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
	}

	nlohmann::json jsonData = nlohmann::json::parse(readBuffer);
	root = jsonData.get<ParseDefs::Root>();
}

size_t YahooFinanceFetcher::WriteCallback(void * contents, size_t size, size_t nmemb, std::string * s)
{
	s->append((char *)(contents), size * nmemb);
	return size * nmemb;
}
