"""PDF compilation from LaTeX source."""

import subprocess
from pathlib import Path
from typing import Tuple


def compile_latex_to_pdf(
    tex_file: Path,
    output_dir: Path = None,
    timeout: int = 60
) -> Tuple[bool, Path, str]:
    """
    Compile a LaTeX file to PDF using pdflatex.

    Args:
        tex_file: Path to the .tex source file
        output_dir: Directory for output files (defaults to tex_file's parent)
        timeout: Max seconds for compilation

    Returns:
        Tuple of (success, pdf_path, error_message)
    """
    tex_file = Path(tex_file)
    if not tex_file.exists():
        return False, Path(""), f"TeX file not found: {tex_file}"

    if output_dir is None:
        output_dir = tex_file.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / tex_file.with_suffix('.pdf').name

    try:
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory", str(output_dir),
                str(tex_file),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(output_dir),
        )

        if pdf_path.exists():
            return True, pdf_path, ""

        error_msg = result.stderr or result.stdout[-500:] if result.stdout else "Unknown pdflatex error"
        return False, pdf_path, f"PDF not generated: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, pdf_path, f"pdflatex timed out after {timeout}s"
    except FileNotFoundError:
        return False, pdf_path, "pdflatex not found. Install a TeX distribution (e.g. MiKTeX or TeX Live)."
    except Exception as exc:
        return False, pdf_path, str(exc)
