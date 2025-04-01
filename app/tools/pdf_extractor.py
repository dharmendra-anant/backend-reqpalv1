import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pymupdf  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class PDFLink:
    """Represents a hyperlink found in a PDF document."""

    uri: str
    text: str
    page_number: int
    link_type: str  # 'uri', 'goto', 'launch', etc.
    rect: Tuple[float, float, float, float]  # position on page


@dataclass
class PDFContent:
    """Represents the structured content extracted from a PDF document."""

    text: List[str]
    links: List[PDFLink]
    metadata: Dict


@dataclass
class DebugOutput:
    """Represents debug output from PDF extraction"""

    text: str
    links_markdown: str


class PDFExtractor:
    """Extracts and structures content from PDF documents."""

    def __init__(self, password: Optional[str] = None) -> None:
        self.password = password

    def extract_content(self, pdf_path: Path, debug: bool = False) -> PDFContent:
        """Extracts text and links from a PDF in a structured format."""
        doc = self._open_secured_document(pdf_path)
        content = self._gather_document_content(doc)
        doc.close()

        if debug:
            debug_output = self._generate_debug_output(content)
            logger.debug(
                "PDF Debug Output",
                extra={
                    "context": {
                        "text": debug_output.text,
                        "links": debug_output.links_markdown,
                        "pdf_path": str(pdf_path),
                    },
                },
            )

        return content

    def _open_secured_document(self, pdf_path: Path) -> pymupdf.Document:
        """Opens and authenticates a PDF document if needed."""
        doc = self._open_document(pdf_path)
        if doc.needs_pass and self.password:
            doc.authenticate(self.password)
        return doc

    def _gather_document_content(self, doc: pymupdf.Document) -> PDFContent:
        """Collects all content from the PDF document."""
        return PDFContent(
            text=self._extract_all_pages_text(doc),
            links=self._extract_all_pages_links(doc),
            metadata=doc.metadata,
        )

    def _extract_all_pages_text(self, doc: pymupdf.Document) -> List[str]:
        """Extracts text content from all pages with embedded markdown links."""
        formatted_pages = []
        for page_num, page in enumerate(doc, 1):
            # Get all links for this page and sort them by their position (top to bottom)
            links = sorted(
                self._extract_page_links(page, page_num),
                key=lambda x: (x.rect[1], x.rect[0]),
            )

            # Build the page text with links in the correct positions
            formatted_text = []
            last_pos = 0

            for link in links:
                # For each link, get all text from top of page (0,0) to the link's y-position
                text_before = page.get_textbox((0, 0, page.rect.width, link.rect[1]))
                if text_before:
                    # Only take text we haven't processed yet (from last_pos onwards)
                    formatted_text.append(text_before[last_pos:])

                # Insert the markdown link
                formatted_text.append(f"[{link.text}]({link.uri})")

                # Update our position tracker
                last_pos = len(text_before)

            # Get any remaining text after the last link
            final_text = page.get_text()
            if final_text[last_pos:]:
                formatted_text.append(final_text[last_pos:])

            formatted_pages.append("".join(formatted_text))

        return formatted_pages

    def _extract_all_pages_links(self, doc: pymupdf.Document) -> List[PDFLink]:
        """Extracts links from all pages."""
        links = []
        for page_num, page in enumerate(doc, 1):
            links.extend(self._extract_page_links(page, page_num))
        return links

    def _extract_page_links(self, page: pymupdf.Page, page_num: int) -> List[PDFLink]:
        """Extracts and structures links from a single page."""
        links = []
        for link in page.get_links():
            if pdf_link := self._create_pdf_link(link, page, page_num):
                links.append(pdf_link)
        return links

    def _create_pdf_link(
        self, link: Dict, page: pymupdf.Page, page_num: int
    ) -> Optional[PDFLink]:
        """Creates a structured PDFLink object from raw link data."""
        uri = link.get("uri", "")
        if not uri:
            return None

        # rect is a tuple of (x0, y0, x1, y1) coordinates defining the link's bounding box on the page
        rect = link.get("from")  # Get the link's rectangle coordinates
        link_text = (
            page.get_textbox(rect) if rect else ""
        )  # Extract text within the rectangle if it exists

        return PDFLink(
            uri=uri,
            text=link_text.strip(),
            page_number=page_num,
            link_type=link.get("type", "unknown"),
            rect=rect if rect else (0.0, 0.0, 0.0, 0.0),
        )

    def _open_document(self, pdf_path: Path) -> pymupdf.Document:
        """Opens a PDF document, ensuring the file exists."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        return pymupdf.open(pdf_path)

    def _generate_debug_output(self, content: PDFContent) -> DebugOutput:
        """Generates debug information for logging."""
        text_output = "\n".join(content.text)

        web_links = [link for link in content.links if link.link_type == "uri"]
        links_by_page = self._group_links_by_page(content.links)

        links_output = self._format_links_as_markdown(web_links)
        links_output += "\n\nBy Page:\n"
        for page_num, page_links in links_by_page.items():
            links_output += f"\nPage {page_num}:\n"
            links_output += self._format_links_as_markdown(page_links)

        return DebugOutput(text=text_output, links_markdown=links_output)

    @staticmethod
    def _group_links_by_page(links: List[PDFLink]) -> Dict[int, List[PDFLink]]:
        """Groups links by their page number."""
        links_by_page: Dict[int, List[PDFLink]] = {}
        for link in links:
            links_by_page.setdefault(link.page_number, []).append(link)
        return links_by_page

    @staticmethod
    def _format_links_as_markdown(links: List[PDFLink]) -> str:
        """Formats links in Markdown format."""
        return "\n".join(f"- [{link.text}]({link.uri})" for link in links)


def extract_text_from_pdf(pdf_path: Path, password: Optional[str] = None) -> PDFContent:
    """Extracts all content from a PDF file."""
    extractor = PDFExtractor(password=password)
    content = extractor.extract_content(pdf_path, debug=True)
    logger.debug(f"Extracted content from {pdf_path}", extra={"content": content})
    return content
