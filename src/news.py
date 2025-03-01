from newsapi import NewsApiClient
from dotenv import load_dotenv
import os

load_dotenv()

class NewsService:
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.newsapi = NewsApiClient(api_key=self.api_key)

    def get_news_by_topic(self, topic, language='es', sort_by='publishedAt', page_size=10):
        """
        Get news articles about a specific topic
        
        Args:
            topic (str): The topic to search for
            language (str): Language of news articles (default: 'es' for Spanish)
            sort_by (str): Sort articles by ('relevancy', 'popularity', 'publishedAt')
            page_size (int): Number of articles to return (max 100)
            
        Returns:
            list: List of news articles
        """
        try:
            response = self.newsapi.get_everything(
                q=topic,
                language=language,
                sort_by=sort_by,
                page_size=page_size
            )
            
            return self._format_articles(response['articles'])
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return []

    def _format_articles(self, articles):
        """Format the articles for better readability"""
        formatted_articles = []
        for i, article in enumerate(articles, 1):
            formatted_article = {
                'number': i,
                'title': article['title'],
                'description': article['description'],
                'source': article['source']['name'],
                'url': article['url'],
                'published_at': article['publishedAt']
            }
            formatted_articles.append(formatted_article)
        return formatted_articles

def display_news(articles):
    """Display the news articles in a readable format"""
    if not articles:
        print("No se encontraron artículos.")
        return

    for article in articles:
        print(f"\n{'-' * 80}")
        print(f"{article['number']}. {article['title']}")
        print(f"Fuente: {article['source']}")
        print(f"Publicado: {article['published_at']}")
        print(f"\nDescripción: {article['description']}")
        print(f"Leer más: {article['url']}")

def main():
    news_service = NewsService()
    
    topic = input("Ingrese un tema para buscar noticias: ")
    
    articles = news_service.get_news_by_topic(topic)
    
    display_news(articles)

if __name__ == "__main__":
    main()
