#!/usr/bin/env python3
import os
from pypdf import PdfReader, PdfWriter  # pip install pypdf

# ←––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# EDIT THESE:
INPUT_DIR  = "C:\\Users\\mingd\\Downloads\\ChatGPT o3"
OUTPUT_DIR = "C:\\Users\\mingd\\Downloads\\ChatGPT o3\\output"
# –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––→

def merge_pdf_pairs(input_dir, output_dir=None):
    # 1) Gather and sort
    pdfs = sorted(f for f in os.listdir(input_dir) if f.lower().endswith('.pdf'))
    if not pdfs:
        print("No PDF files found in", input_dir)
        return

    # 2) Prepare output folder
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = input_dir

    # 3) Merge in pairs
    for i in range(0, len(pdfs), 2):
        if i + 1 >= len(pdfs):
            print(f"Skipping unpaired file: {pdfs[i]}")
            break

        a, b = pdfs[i], pdfs[i+1]
        title_a, title_b = os.path.splitext(a)[0], os.path.splitext(b)[0]

        writer = PdfWriter()
        # append all pages from both PDFs
        for fname in (a, b):
            reader = PdfReader(os.path.join(input_dir, fname))
            for page in reader.pages:
                writer.add_page(page)

        # set the combined Title metadata
        writer.add_metadata({"/Title": f"{title_a} {title_b}"})

        out_name = f"{title_a}_{title_b}.pdf"
        out_path = os.path.join(output_dir, out_name)
        with open(out_path, "wb") as fout:
            writer.write(fout)

        print(f"Merged {a} + {b} → {out_name}")

if __name__ == "__main__":
    merge_pdf_pairs(INPUT_DIR, OUTPUT_DIR)
