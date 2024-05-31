#include "ParseDefs.h"

class YahooFinanceFetcher
{
public:
	YahooFinanceFetcher();
	~YahooFinanceFetcher();

	void fetchData(const std::string & symbol, const std::string & range, ParseDefs::Root & root);

private:
	static size_t WriteCallback(void * contents, size_t size, size_t nmemb, std::string * s);

private:
	void * m_curl_handle;
};
