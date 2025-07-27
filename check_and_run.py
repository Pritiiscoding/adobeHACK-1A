import os
import sys
from PyPDF2 import PdfReader

def check_pdf(filepath):
    try:
        with open(filepath, 'rb') as f:
            reader = PdfReader(f)
            print(f"PDF file is valid. Number of pages: {len(reader.pages)}")
            if hasattr(reader, 'outline') and reader.outline:
                print("This PDF has an outline.")
                return True
            else:
                print("This PDF does not have an outline.")
                return False
    except Exception as e:
        print(f"Error checking PDF: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the path to a PDF file.")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if check_pdf(pdf_path):
        print("\nRunning outline extractor...")
        os.system(f'python main.py "{pdf_path}" -o "output/outline.json"')
