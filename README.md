# Backend Service

A Python backend service for processing documents and extracting information.

## Features
- PDF text extraction with support for password-protected documents
- Hyperlink extraction from PDFs with page numbers and positions
- Markdown-formatted link output
- Debug output support

## Setup

### Using UV (Recommended)

1. Install UV:
```bash
pip install uv
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
uv pip install -e .
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY=your_key_here
```

### Using pip (Alternative)

If you prefer using traditional pip:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -e .
```

## Using the CLI

1. Create required directories if they don't exist:
```bash
mkdir -p scratch logs
```

2. Add your resumes to process:
```bash
# Copy any PDF resumes you want to process into the scratch directory
cp path/to/your/resume.pdf scratch/
```

3. Activate your virtual environment:
```bash
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

4. Run the CLI:
```bash
python main.py
```

The CLI will:
- Show you available PDF files in the scratch directory
- Let you select which file to process
- Display results in the console
- Save detailed JSON output to `logs/app.log`

### Password-Protected PDFs

If your PDF is password-protected:

```python
extractor = PDFExtractor(password="your_password")
content = extractor.extract_content(Path("scratch/protected.pdf"))
```

## Development

### Dependency Management

We use UV for dependency management. To add new dependencies:

1. Either:
   - Add directly to `pyproject.toml`, or
   - Run `uv add package-name`

2. Sync dependencies:
```bash
uv sync
```

## Output Format

The extractor provides structured output:

- Text: Raw text content from each page
- Links: Structured link information including:
  - URI
  - Link text
  - Page number
  - Link type (URI, internal reference, etc.)
  - Position coordinates on the page
- Metadata: PDF document metadata

## Debugging

Enable debug mode to generate detailed output files:
- `scratch/text.txt`: Contains all extracted text
- `scratch/links.md`: Contains formatted hyperlinks found in the document
