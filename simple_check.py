import sys
from PyPDF2 import PdfReader

def main():
    if len(sys.argv) < 2:
        print("Please provide the path to a PDF file.")
        return 1
    
    pdf_path = sys.argv[1]
    print(f"Checking PDF: {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            print(f"Number of pages: {len(reader.pages)}")
            
            if hasattr(reader, 'outline') and reader.outline:
                print("\nOutline found!")
                print("\nOutline structure:")
                print(reader.outline)
                
                # Extract outline to a file
                with open('output/outline_content.txt', 'w', encoding='utf-8') as out_file:
                    out_file.write(str(reader.outline))
                print("\nOutline content saved to output/outline_content.txt")
            else:
                print("\nNo outline found in the PDF.")
                
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
