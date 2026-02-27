"""
PDF export service using WeasyPrint.
Renders the soap_pdf.html template to a PDF byte stream and returns
an HttpResponse with the correct Content-Disposition header.

WeasyPrint requires native system libraries (libpango, libcairo, libgobject).
The import is intentionally lazy (inside the function) so Django starts up
correctly on macOS dev machines that don't have those libs installed.
In Docker / Render, the Dockerfile installs all required libs via apt-get.
"""

import logging

from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def generate_pdf_bytes(encounter) -> bytes:
    """Render the SOAP note template and convert to PDF bytes."""
    import weasyprint  # lazy import — requires native libs only available in Docker

    html_string = render_to_string(
        "encounters/soap_pdf.html",
        {
            "encounter": encounter,
            "soap_note": encounter.soap_note,
            "transcript": encounter.transcript,
        },
    )
    return weasyprint.HTML(string=html_string).write_pdf()


def get_pdf_response(encounter) -> HttpResponse:
    """Return an HttpResponse that triggers a PDF file download."""
    pdf_bytes = generate_pdf_bytes(encounter)
    filename = f"soap_note_{str(encounter.id)[:8]}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
