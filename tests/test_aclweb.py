from paper_crawler.factories.title_factory import TitleCrawlerFactory
from paper_crawler.title_crawlers.aclweb import AclwebPaperTitleCrawler


def test_aclweb_extract_titles():
    html = """
    <html>
      <body>
        <div class="page__content">
          <ul>
            <li><strong>First ACL Paper</strong></li>
            <li><strong>Second ACL Paper</strong></li>
            <li><strong>Second ACL Paper</strong></li>
          </ul>
        </div>
      </body>
    </html>
    """

    crawler = AclwebPaperTitleCrawler()
    soup = crawler.parse_html(html)
    items = crawler.extract_items(soup, "https://2025.aclweb.org/program")

    assert items == [
        {"title": "First ACL Paper"},
        {"title": "Second ACL Paper"},
    ]


def test_factory_create_aclweb():
    crawler = TitleCrawlerFactory.create("https://2025.aclweb.org/program")
    assert isinstance(crawler, AclwebPaperTitleCrawler)


def test_factory_create_aclweb_for_2024():
    crawler = TitleCrawlerFactory.create("https://2024.aclweb.org/program")
    assert isinstance(crawler, AclwebPaperTitleCrawler)
