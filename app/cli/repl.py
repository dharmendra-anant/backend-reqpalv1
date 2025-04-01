import typer

from app.cli.commands.process_pdf import extract_test_from_pdf
from app.cli.commands.process_resume import score_resume_against_jd

app = typer.Typer(help="Resume processing CLI tool")


app.command()(extract_test_from_pdf)
app.command()(score_resume_against_jd)

if __name__ == "__main__":
    typer.run(app)
