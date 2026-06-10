"""
Extract AP FRQ questions and Scoring Guidelines from College Board PDFs.

Usage:
    python scripts/extract_frq_pdfs.py --year 2024 --exam ab --type frq
    python scripts/extract_frq_pdfs.py --year 2024 --exam ab --type sg
    python scripts/extract_frq_pdfs.py --year 2024 --exam ab --type both

Requires: PyMuPDF (pip install pymupdf)
Downloads PDFs via WebFetch cache or from apcentral.collegeboard.org,
then extracts text using PyMuPDF.

Output goes to scripts/output/frq_extracts/
"""

import argparse
import os
import sys
import fitz  # PyMuPDF


# Known URL patterns by year range
def get_frq_url(year, exam):
    """Get the FRQ PDF URL for a given year and exam type."""
    yy = str(year)[2:]  # e.g., "24" from 2024
    exam = exam.lower()
    if year >= 2020:
        return f"https://apcentral.collegeboard.org/media/pdf/ap{yy}-frq-calculus-{exam}.pdf"
    elif year == 2019:
        return f"https://apcentral.collegeboard.org/media/pdf/ap19-frq-calculus-{exam}.pdf"
    elif year == 2018:
        return f"https://apcentral.collegeboard.org/media/pdf/ap18-frq-calculus-{exam}.pdf"
    elif year == 2017:
        return f"https://apcentral.collegeboard.org/media/pdf/ap-calculus-{exam}-frq-2017.pdf"
    else:
        return None


def get_sg_url(year, exam):
    """Get the Scoring Guidelines PDF URL for a given year and exam type."""
    yy = str(year)[2:]
    exam = exam.lower()
    if year >= 2020:
        return f"https://apcentral.collegeboard.org/media/pdf/ap{yy}-sg-calculus-{exam}.pdf"
    elif year == 2019:
        return f"https://apcentral.collegeboard.org/media/pdf/ap19-sg-calculus-{exam}.pdf"
    elif year == 2018:
        return f"https://apcentral.collegeboard.org/media/pdf/ap18-sg-calculus-{exam}.pdf"
    elif year == 2017:
        return f"https://apcentral.collegeboard.org/media/pdf/ap-calculus-{exam}-sg-2017.pdf"
    else:
        return None


def extract_pdf_text(pdf_path):
    """Extract all text from a PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(doc.page_count):
        text = doc[i].get_text()
        pages.append(text)
    doc.close()
    return pages


def save_extract(pages, output_path):
    """Save extracted text to a file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, text in enumerate(pages):
            f.write(f"\n=== Page {i + 1} ===\n")
            f.write(text)
    print(f"Saved: {output_path} ({len(pages)} pages)")


def main():
    parser = argparse.ArgumentParser(description="Extract AP FRQ PDFs")
    parser.add_argument('--year', type=int, required=True, help='Exam year (2017-2024)')
    parser.add_argument('--exam', required=True, choices=['ab', 'bc'], help='AB or BC exam')
    parser.add_argument('--type', required=True, choices=['frq', 'sg', 'both'],
                        help='frq=questions, sg=scoring guidelines, both=both')
    parser.add_argument('--pdf-dir', default=None,
                        help='Directory containing already-downloaded PDFs')
    args = parser.parse_args()

    output_dir = os.path.join(os.path.dirname(__file__), 'output', 'frq_extracts')
    os.makedirs(output_dir, exist_ok=True)

    types_to_extract = ['frq', 'sg'] if args.type == 'both' else [args.type]

    for doc_type in types_to_extract:
        if doc_type == 'frq':
            url = get_frq_url(args.year, args.exam)
        else:
            url = get_sg_url(args.year, args.exam)

        if not url:
            print(f"No URL pattern for year {args.year}")
            sys.exit(1)

        # Check if PDF already exists locally
        pdf_filename = f"ap{args.year}-{doc_type}-calculus-{args.exam}.pdf"
        pdf_path = None

        if args.pdf_dir:
            candidate = os.path.join(args.pdf_dir, pdf_filename)
            if os.path.exists(candidate):
                pdf_path = candidate

        if not pdf_path:
            # Look in output dir
            candidate = os.path.join(output_dir, pdf_filename)
            if os.path.exists(candidate):
                pdf_path = candidate

        if not pdf_path:
            print(f"PDF not found locally: {pdf_filename}")
            print(f"Download URL: {url}")
            print(f"Save to: {os.path.join(output_dir, pdf_filename)}")
            print("Use WebFetch or browser to download, then re-run.")
            continue

        # Extract text
        print(f"Extracting: {pdf_path}")
        pages = extract_pdf_text(pdf_path)

        # Save extracted text
        output_filename = f"{args.year}_{args.exam}_{doc_type}.txt"
        output_path = os.path.join(output_dir, output_filename)
        save_extract(pages, output_path)


if __name__ == '__main__':
    main()
