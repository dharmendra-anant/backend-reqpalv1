import asyncio
from pathlib import Path
from typing import List, Optional

import typer

from app.agents.resume_processor import ResumeProcessorAgent


def scan_directory_for_pdfs(scratch_dir: Path) -> List[Path]:
    """Get PDF files from scratch directory."""
    pdf_files = list(scratch_dir.glob("*.pdf"))

    if not pdf_files:
        typer.echo(
            "No PDF files found in scratch directory. Add some PDFs there and try again."
        )
        raise typer.Exit(1)

    return pdf_files


def display_and_choose_pdf(pdf_files: List[Path]) -> Path:
    """Prompt user to select a PDF file."""
    typer.echo("\nAvailable PDF files:")
    typer.echo("\n".join(f"[{i}] {pdf.name}" for i, pdf in enumerate(pdf_files)))
    choice = typer.prompt("Select file number", type=int, show_choices=False)
    return pdf_files[choice]


async def extract_pdf_content(pdf_path: Path) -> None:
    """Process and extract content from the PDF file."""
    processor = ResumeProcessorAgent()
    await processor.run(pdf_path)
    typer.echo(f"\nProcessed: {pdf_path.name}")


def extract_test_from_pdf(
    pdf_path: Optional[Path] = typer.Argument(
        None,
        help="Path to PDF file to process",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
) -> None:
    """Process a single PDF file to extract its content."""
    while True:
        try:
            if pdf_path is None:
                typer.echo("\n=== PDF Processing Menu ===")
                typer.echo("[p] Process file")
                typer.echo("[q] Quit")

                choice = typer.prompt("Select option", type=str).lower()

                if choice == "q":
                    typer.echo("Goodbye!")
                    break
                elif choice == "p":
                    pdf_files = scan_directory_for_pdfs(Path("scratch"))
                    selected_pdf = display_and_choose_pdf(pdf_files)
                    asyncio.run(extract_pdf_content(selected_pdf))
                else:
                    typer.echo("Invalid option. Please try again.")
            else:
                # Direct file processing mode
                asyncio.run(extract_pdf_content(pdf_path))
                break

        except (ValueError, IndexError):
            typer.echo("Invalid selection. Please try again.")
