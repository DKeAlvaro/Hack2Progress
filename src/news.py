import sys
from newsapi import NewsApiClient
from dotenv import load_dotenv
import os
from openai import OpenAI

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


def summarize_news(articles):
    client = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Eres un experto en resumir noticias."},
            {"role": "user", "content": "Dadas las siguientes noticias, devuelve el impacto que tendrán en la población sobre si generará movilidad en la ciudad (e.g un concierto generará alta movilidad, una convencion de yoga baja movilidad, etc.) alto, bajo o medio. Si es alto, también devuelve el motivo:  " + str(articles)},
        ],
        stream=False
    )

    return response.choices[0].message.content



def main():
    news_service = NewsService()
    
    topic = input("Ingrese un tema para buscar noticias: ")
    
    articles = news_service.get_news_by_topic(topic)
    
    with open('news_output.txt', 'w') as file:
        original_stdout = sys.stdout
        sys.stdout = file
        try:
            display_news(articles)
            print(summarize_news(articles))
        finally:
            sys.stdout = original_stdout

if __name__ == "__main__":
    main()
