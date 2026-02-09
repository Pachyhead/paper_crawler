from paper_crawler.factory import CrawlerFactory
from paper_crawler.sites.aclweb import Aclweb


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

    crawler = Aclweb()
    soup = crawler.parse_html(html)
    items = crawler.extract_items(soup, "https://2025.aclweb.org/program")

    assert items == [
        {"title": "First ACL Paper"},
        {"title": "Second ACL Paper"},
    ]


def test_factory_create_aclweb():
    crawler = CrawlerFactory.create("https://2025.aclweb.org/program")
    assert isinstance(crawler, Aclweb)
