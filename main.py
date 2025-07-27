import json
import os
import pdfplumber
import logging
import time
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
from jsonschema import validate, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pdf_processor.log')
    ]
)
logger = logging.getLogger(__name__)

# Define the output schema
OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["title", "outline"],
    "properties": {
        "title": {"type": "string"},
        "outline": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["level", "text", "page"],
                "properties": {
                    "level": {"type": "string", "enum": ["H1", "H2", "H3"]},
                    "text": {"type": "string"},
                    "page": {"type": "integer", "minimum": 1}
                }
            }
        }
    }
}

def validate_output(output_data: Dict[str, Any]) -> bool:
    """Validate output against schema."""
    try:
        validate(instance=output_data, schema=OUTPUT_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"Output validation failed: {e.message}")
        return False

def cluster_font_sizes(sizes: List[float], k: int = 4) -> List[float]:
    """Cluster font sizes into k groups and return representative sizes."""
    if not sizes:
        return []
    
    unique_sizes = sorted(set(sizes), reverse=True)
    
    if len(unique_sizes) <= k:
        return unique_sizes + [unique_sizes[-1]] * (k - len(unique_sizes)) if unique_sizes else []
    
    # Simple binning approach
    chunk_size = max(1, len(unique_sizes) // k)
    clusters = []
    
    for i in range(k):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size if i < k - 1 else len(unique_sizes)
        cluster = unique_sizes[start_idx:end_idx]
        if cluster:
            clusters.append(cluster[len(cluster) // 2])  # Use median as representative
    
    return sorted(clusters, reverse=True)

def extract_outline(pdf_path: str) -> Dict[str, Any]:
    """
    Extract document title and hierarchical outline from PDF.
    
    Returns:
        dict: {
            'title': str,
            'outline': [{'level': str, 'text': str, 'page': int}, ...]
        }
    """
    start_time = time.time()
    logger.info(f"Processing PDF: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_sizes = []
            lines_data = []
            
            # Check if PDF is encrypted
            try:
                if hasattr(pdf, 'stream') and hasattr(pdf.stream, 'encrypted') and pdf.stream.encrypted:
                    logger.warning("PDF is encrypted, trying to decrypt with empty password")
                    try:
                        pdf.stream.decrypt('')
                    except Exception as e:
                        logger.error(f"Failed to decrypt PDF: {str(e)}")
                        return {'title': '', 'outline': []}
            except Exception as e:
                logger.warning(f"Could not check PDF encryption status: {str(e)}")
                # Continue processing anyway
            
            # Process pages in batches for memory efficiency
            for pg_no, page in enumerate(pdf.pages, 1):
                if time.time() - start_time > 9:  # Timeout after 9 seconds
                    logger.warning(f"Processing timeout after {pg_no} pages")
                    break
                    
                try:
                    # Try to extract text with different methods if needed
                    text = page.extract_text()
                    
                    if not text or len(text.strip()) < 10:  # If no text or very little text
                        logger.warning(f"Little or no text found on page {pg_no}, trying alternative extraction method")
                        # Try alternative extraction method
                        text = page.extract_text(x_tolerance=3, y_tolerance=3)
                        
                        # If still no text, try to extract words
                        if not text or len(text.strip()) < 10:
                            words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
                            if words:
                                text = ' '.join(w['text'] for w in words)
                    
                    # If we have text, process it
                    if text and len(text.strip()) > 10:
                        # Get font information
                        chars = page.chars
                        if chars:
                            # Group characters by line
                            lines = {}
                            for ch in chars:
                                y = round(ch['top'], 1)
                                if y not in lines:
                                    lines[y] = []
                                lines[y].append(ch)
                            
                            # Process each line
                            for y, char_group in lines.items():
                                if not char_group:
                                    continue
                                
                                # Calculate average font size for the line
                                sizes = [c['size'] for c in char_group if 'size' in c]
                                if not sizes:
                                    continue
                                    
                                avg_size = sum(sizes) / len(sizes)
                                line_text = ''.join(c['text'] for c in sorted(char_group, key=lambda x: x['x0']))
                                
                                if line_text.strip():
                                    all_sizes.append(avg_size)
                                    lines_data.append((pg_no, line_text.strip(), avg_size))
                        else:
                            # Fallback: if no character info, just use the extracted text
                            logger.warning("No character information available, using plain text extraction")
                            for line in text.split('\n'):
                                if line.strip():
                                    lines_data.append((pg_no, line.strip(), 12))  # Default size
                
                except Exception as e:
                    logger.error(f"Error processing page {pg_no}: {str(e)}")
                    continue
            
            if not lines_data:
                logger.error("No text content found in PDF. The PDF might be a scanned document or use non-standard encoding.")
                # Try one more time with OCR-like extraction
                try:
                    logger.info("Attempting alternative text extraction...")
                    text = ''
                    for page in pdf.pages:
                        text += page.extract_text() or ''
                    
                    if text and len(text.strip()) > 10:
                        logger.info("Alternative extraction successful")
                        for i, line in enumerate(text.split('\n')):
                            if line.strip():
                                lines_data.append((1, line.strip(), 12))  # Default size
                except Exception as e:
                    logger.error(f"Alternative extraction failed: {str(e)}")
                
                if not lines_data:
                    return {'title': '', 'outline': []}
            
            # Cluster font sizes
            representative_sizes = cluster_font_sizes(all_sizes, k=4)
            while len(representative_sizes) < 4:
                representative_sizes.append(representative_sizes[-1] if representative_sizes else 12)
                
            title_font, h1_font, h2_font, h3_font = representative_sizes[:4]
            
            # Extract title (first non-empty line with largest font)
            title = next((text for _, text, size in lines_data if size >= title_font * 0.9), 
                        lines_data[0][1] if lines_data else "")
            
            # Build outline
            outline = []
            for pg_no, text, font_size in lines_data:
                # Skip title line
                if text == title:
                    continue
                
                level = None
                if font_size >= h1_font * 0.9:
                    level = 'H1'
                elif font_size >= h2_font * 0.9:
                    level = 'H2'
                elif font_size >= h3_font * 0.9:
                    level = 'H3'
                
                # Filter out noise
                if level and len(text) > 2 and not text.isdigit():
                    outline.append({
                        'level': level,
                        'text': text,
                        'page': pg_no
                    })
            
            result = {
                'title': title,
                'outline': outline
            }
            
            # Validate output
            if not validate_output(result):
                logger.warning("Output validation failed, but returning the result anyway")
                
            logger.info(f"Processed {len(lines_data)} lines, found {len(outline)} headings in {time.time() - start_time:.2f} seconds")
            return result
            
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return {'title': '', 'outline': []}

def main():
    """Main function to process all PDFs in input directory."""
    input_dir = '/app/input'
    output_dir = '/app/output'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} does not exist")
        return
    
    # Process all PDF files in input directory
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    for filename in pdf_files:
        start_time = time.time()
        pdf_path = os.path.join(input_dir, filename)
        
        try:
            # Extract outline
            result = extract_outline(pdf_path)
            
            # Save result as JSON
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_final_outline.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Processed {filename} in {time.time() - start_time:.2f} seconds -> {output_filename}")
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {str(e)}")
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()