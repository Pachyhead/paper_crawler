from paper_crawler.factories.title_factory import TitleCrawlerFactory
from paper_crawler.title_crawlers.dblp import DblpPaperTitleCrawler


def test_dblp_extract_titles():
    html = """
    <html>
      <body>
        <ul class="publ-list">
          <li class="entry inproceedings">
            <cite><span class="title">Paper One: A Study.</span></cite>
          </li>
          <li class="entry inproceedings">
            <cite><span class="title">Paper Two.</span></cite>
          </li>
          <li class="entry inproceedings">
            <cite><span class="title">Paper Two.</span></cite>
          </li>
          <li class="entry inproceedings">
            <cite><span class="title">  Paper   Three   </span></cite>
          </li>
        </ul>
      </body>
    </html>
    """

    crawler = DblpPaperTitleCrawler()
    soup = crawler.parse_html(html)
    items = crawler.extract_items(soup, "https://dblp.org/db/conf/emnlp/emnlp2025.html")

    assert items == [
        {"title": "Paper One: A Study."},
        {"title": "Paper Two."},
        {"title": "Paper   Three"},
    ]


def test_dblp_crawl_pipeline_normalizes_and_adds_meta():
    html = """
    <html>
      <body>
        <li class="entry inproceedings"><span class="title">A   B</span></li>
      </body>
    </html>
    """

    class FakeDblp(DblpPaperTitleCrawler):
        def fetch_html(self, url: str) -> str:
            return html

    url = "https://dblp.org/db/conf/emnlp/emnlp2025.html"
    items = FakeDblp().crawl(url)

    assert items == [
        {
            "title": "A B",
            "source_url": url,
            "crawler": "dblp",
        }
    ]


def test_factory_create_dblp():
    crawler = TitleCrawlerFactory.create("https://dblp.org/db/conf/emnlp/emnlp2025.html")
    assert isinstance(crawler, DblpPaperTitleCrawler)


def test_factory_create_dblp_with_www():
    crawler = TitleCrawlerFactory.create("https://www.dblp.org/db/conf/emnlp/emnlp2025.html")
    assert isinstance(crawler, DblpPaperTitleCrawler)
