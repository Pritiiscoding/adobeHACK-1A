import os
import shutil
import subprocess

# Source and destination paths
source_pdf = r"C:\Users\Prity Kumari\Downloads\file01.pdf"
dest_dir = "input"
dest_pdf = os.path.join(dest_dir, "file01.pdf")

# Create input directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Copy the file
print(f"Copying {source_pdf} to {dest_pdf}")
shutil.copy2(source_pdf, dest_pdf)

# Run the outline extractor
print("Running outline extractor...")
subprocess.run(["python", "main.py", dest_pdf, "-o", "output/outline.json"], check=True)
