from utils.config import bronze_logger, session
from utils.api_utils import APIUtils
import finnhub
from datetime import datetime
from typing import List, Dict

class FinnhubNewsAPIFetcher:
    BASE_URL: str = "https://finnhub.io/api/v1"
    finnhub_client = finnhub.Client(api_key=APIUtils._get_api_key("API_FINHUB_NEWS_KEY"))
    
    @classmethod
    def fetch_market_holiday(cls, exchange: str = "US") -> Dict:
        """
        Fetch market holiday information for a specified exchange.

        This class method retrieves market holiday details by calling the
        `market_holiday` method on the `finnhub_client` associated with the class.
        It allows users to specify an exchange code to obtain the relevant holiday data.

        Args:
            exchange (str): The market exchange identifier (e.g., "US") for which
                holiday information is requested. Defaults to "US".

        Returns:
            Dict: A dictionary containing market holiday details for the given exchange.
        """
        return cls.finnhub_client.market_holiday(exchange = exchange)
        
    
    @classmethod
    def fetch_finnhub_news(cls, symbols: List[str], max_company_articles: int = 50, max_market_articles: int = 20) -> Dict:
        """
        Fetches company-specific and market-wide news from Finnhub API from 2016 to today
        
        Args:
            symbols (list): List of stock tickers (e.g., ['AAPL', 'TSLA'])
            max_company_articles (int): Max articles per company
            max_market_articles (int): Max market news articles
        
        Returns:
            dict: Structured news data with company and market news
        """
        from_date = datetime(2016, 1, 1)
        to_date = datetime.today()
        
        news_data = {
            'company_news': {},
            'market_news': [],
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'symbol_count': len(symbols),
                'date_range': {
                    'start': from_date.isoformat(),
                    'end': to_date.isoformat()
                }
            }
        }

        def process_article(article: Dict, news_type: str = 'company') -> Dict:
            """Process raw article data into standardized format"""
            dt = datetime.fromtimestamp(article['datetime']) if 'datetime' in article else None
            return {
                'id': article.get('id', ''),
                'category': article.get('category', 'general'),
                'sector': article.get('sector', ''),
                'published': dt.isoformat() if dt else None,
                'headline': article.get('headline', ''),
                'summary': article.get('summary', '')[:500] + '...' if article.get('summary') else '',
                'url': article.get('url', ''),
                'sentiment': round(article.get('sentiment', 0), 2),
                'relevance': round(article.get('relevance', 0), 2),
                'source': article.get('source', ''),
                'symbols': article.get('relatedTickers', []),
                'type': news_type
            }

        for symbol in symbols:
            try:
                raw_news = cls.finnhub_client.company_news(
                    symbol=symbol,
                    _from=from_date.strftime('%Y-%m-%d'),
                    to=to_date.strftime('%Y-%m-%d')
                )
                
                processed = [
                    process_article(article, 'company') 
                    for article in raw_news[:max_company_articles]
                    if article.get('headline')
                ]
                
                news_data['company_news'][symbol] = {
                    'count': len(processed),
                    'articles': processed
                }
                bronze_logger.info(f"Fetched {len(processed)} articles for {symbol}")

            except Exception as e:
                error_msg = f"Error fetching news for {symbol}: {str(e)}"
                bronze_logger.error(error_msg)
                news_data['company_news'][symbol] = {
                    'count': 0,
                    'articles': [],
                    'error': error_msg
                }

        try:
            market_news = cls.finnhub_client.market_news(category='general')
            processed_market = [
                process_article(article, 'market')
                for article in market_news[:max_market_articles]
                if article.get('headline')
            ]
            news_data['market_news'] = processed_market
            bronze_logger.info(f"Fetched {len(processed_market)} market articles")

        except Exception as e:
            error_msg = f"Error fetching market news: {str(e)}"
            bronze_logger.error(error_msg)
            news_data['market_news_error'] = error_msg

        return news_data

if __name__ == "__main__":
    news_data = FinnhubNewsAPIFetcher.fetch_finnhub_news(["AAPL"])
    print(news_data)