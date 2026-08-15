from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
STYLES = ROOT / "styles.css"
FAVICON = ROOT / "favicon.svg"


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.start_tags = []
        self.text = []
        self.title = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.start_tags.append((tag, attributes))
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        stripped = " ".join(data.split())
        if stripped:
            self.text.append(stripped)
            if self._in_title:
                self.title.append(stripped)


def parsed_site():
    parser = SiteParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    return parser


class SiteDocumentTests(unittest.TestCase):
    def test_metadata_matches_public_identity(self):
        parser = parsed_site()
        self.assertEqual(" ".join(parser.title), "Jorge Castilla — Founding Software Engineer")
        html = next(attrs for tag, attrs in parser.start_tags if tag == "html")
        self.assertEqual(html.get("lang"), "en")

        metas = [attrs for tag, attrs in parser.start_tags if tag == "meta"]
        links = [attrs for tag, attrs in parser.start_tags if tag == "link"]
        self.assertIn(
            {
                "name": "description",
                "content": "Jorge Castilla is a Founding Software Engineer at Solum Health, building AI systems for healthcare operations.",
            },
            metas,
        )
        self.assertIn(
            {"rel": "canonical", "href": "https://jorgecastilla.com/"},
            links,
        )

    def test_approved_biography_is_present(self):
        text = " ".join(parsed_site().text)
        self.assertIn(
            "Hi, I’m Jorge Castilla. I studied Electronic Engineering, but I’ve spent my career building software. I love building useful things and turning ideas into products.",
            text,
        )
        self.assertIn(
            "I’m currently the Founding Software Engineer at Solum Health, where I build AI systems for healthcare operations—from voice agents to workflow automation for medical practices across the United States.",
            text,
        )

    def test_semantic_page_structure_is_present(self):
        tags = [tag for tag, _ in parsed_site().start_tags]
        self.assertEqual(tags.count("main"), 1)
        self.assertEqual(tags.count("h1"), 1)
        self.assertEqual(tags.count("h2"), 2)
        self.assertEqual(tags.count("nav"), 1)

    def test_social_and_email_destinations_are_exact(self):
        anchors = [attrs for tag, attrs in parsed_site().start_tags if tag == "a"]
        by_href = {anchor["href"]: anchor for anchor in anchors}
        external = {
            "https://github.com/jorgedcb",
            "https://www.linkedin.com/in/jorgecastillab/",
            "https://x.com/Jorgecastillab",
        }
        self.assertEqual(set(by_href), external | {"mailto:jecb2001@gmail.com"})
        for href in external:
            self.assertEqual(by_href[href].get("target"), "_blank")
            self.assertEqual(set(by_href[href].get("rel", "").split()), {"noopener", "noreferrer"})

    def test_page_has_no_runtime_javascript(self):
        tags = [tag for tag, _ in parsed_site().start_tags]
        self.assertNotIn("script", tags)


class SitePresentationTests(unittest.TestCase):
    def test_stylesheet_and_favicon_are_local(self):
        parser = parsed_site()
        links = [attrs for tag, attrs in parser.start_tags if tag == "link"]
        self.assertIn({"rel": "stylesheet", "href": "styles.css"}, links)
        self.assertIn({"rel": "icon", "href": "favicon.svg", "type": "image/svg+xml"}, links)
        self.assertTrue(STYLES.is_file())
        self.assertTrue(FAVICON.is_file())

    def test_accessible_responsive_css_contract(self):
        css = STYLES.read_text(encoding="utf-8")
        for contract in (
            ":root",
            "--color-background",
            "--color-terminal",
            ":focus-visible",
            "@media (max-width: 40rem)",
            "@media (prefers-reduced-motion: reduce)",
            ".cursor",
            "animation: none",
        ):
            self.assertIn(contract, css)


if __name__ == "__main__":
    unittest.main()
