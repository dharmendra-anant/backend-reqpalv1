import asyncio
from pathlib import Path
from typing import List, Tuple

import typer

from app.agents.resume_processor import ResumeProcessorAgent
from app.documents.job_description import JobDescription
from app.documents.resume import Resume


def get_files(scratch_dir: Path) -> Tuple[List[Path], List[Path]]:
    """Get PDF and MD files from scratch directory."""
    pdf_files = list(scratch_dir.glob("*.pdf"))
    md_files = list(scratch_dir.glob("*.md"))

    if not pdf_files or not md_files:
        typer.echo(
            "Need both PDF (resume) and MD (job description) files in scratch directory."
        )
        raise typer.Exit(1)

    return pdf_files, md_files


def select_files(pdf_files: List[Path], md_files: List[Path]) -> Tuple[Path, Path]:
    """Prompt user to select resume and job description files."""
    # Select resume
    typer.echo("\nSelect Resume:")
    typer.echo("\n".join(f"[{i}] {pdf.name}" for i, pdf in enumerate(pdf_files)))
    pdf_choice = typer.prompt("Select resume number", type=int)

    # Select job description
    typer.echo("\nSelect Job Description:")
    typer.echo("\n".join(f"[{i}] {md.name}" for i, md in enumerate(md_files)))
    md_choice = typer.prompt("Select job description number", type=int)

    return pdf_files[pdf_choice], md_files[md_choice]


async def process_files(resume_path: Path, job_desc_path: Path) -> None:
    """Process the selected files."""
    processor = ResumeProcessorAgent(test_mode=False)
    result = await processor.execute(
        resume=Resume(file_path=resume_path),
        job_description=JobDescription(file_path=job_desc_path),
    )
    typer.echo(f"\nProcessing completed. Result: {result}\n")


def score_resume_against_jd() -> None:
    """Run resume processor in test mode with sample files."""
    scratch_dir = Path("scratch")

    while True:
        typer.echo("\n=== Resume Processing Menu ===")
        typer.echo("[p] Process files")
        typer.echo("[q] Quit")

        choice = typer.prompt("Select option", type=str).lower()

        if choice == "q":
            typer.echo("Goodbye!")
            break
        elif choice == "p":
            try:
                pdf_files, md_files = get_files(scratch_dir)
                resume_path, job_desc_path = select_files(pdf_files, md_files)
                asyncio.run(process_files(resume_path, job_desc_path))
            except (ValueError, IndexError):
                typer.echo("Invalid selection. Please try again.")
        else:
            typer.echo("Invalid option. Please try again.")
