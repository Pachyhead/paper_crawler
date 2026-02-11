from paper_crawler.factories.title_factory import TitleCrawlerFactory
from paper_crawler.title_crawlers.example_static import ExampleStaticPaperTitleCrawler


def test_example_static_extract_items():
    html = """
    <html>
      <body>
        <article class="paper-card">
          <h2 class="title">Paper A</h2>
          <a class="title-link" href="/paper-a">Go</a>
          <span class="author">Alice</span>
          <span class="author">Bob</span>
          <time class="published-at">2026-01-01</time>
          <p class="abstract">Sample abstract.</p>
        </article>
      </body>
    </html>
    """

    crawler = ExampleStaticPaperTitleCrawler()
    soup = crawler.parse_html(html)
    items = crawler.extract_items(soup, "https://example.com/papers")

    assert len(items) == 1
    assert items[0]["title"] == "Paper A"
    assert items[0]["url"] == "https://example.com/paper-a"
    assert items[0]["authors"] == "Alice, Bob"


def test_factory_create():
    crawler = TitleCrawlerFactory.create("https://example.com/papers")
    assert isinstance(crawler, ExampleStaticPaperTitleCrawler)


def test_factory_create_with_www_domain():
    crawler = TitleCrawlerFactory.create("https://www.example.com/papers")
    assert isinstance(crawler, ExampleStaticPaperTitleCrawler)


def test_site_specific_request_delay():
    crawler = ExampleStaticPaperTitleCrawler()
    assert crawler.request_delay_seconds == 4.0
