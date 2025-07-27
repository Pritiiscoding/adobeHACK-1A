# PDF Outline Extractor

A high-performance PDF processing solution for extracting document outlines and structure. This project was developed as a submission for the Adobe India Hackathon 2025 Challenge 1a.

## Features

- Extracts hierarchical document structure (title and headings) from PDFs
- Processes PDFs in batch from an input directory
- Generates structured JSON output for each PDF
- Lightweight and efficient implementation
- Validates output against a strict schema
- Runs in a Docker container with no internet access required
- Processes 50+ page PDFs in under 10 seconds

## Prerequisites

- Docker (with support for Linux/AMD64 containers)
- At least 16GB of RAM (as per challenge requirements)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd pdf-outline-extractor
   ```

2. Build the Docker image:
   ```bash
   docker build --platform linux/amd64 -t pdf-outline-extractor .
   ```

## Usage

### Basic Usage

1. Place your PDF files in the `input` directory
2. Run the container:
   ```bash
   docker run --rm \
     -v $(pwd)/input:/app/input:ro \
     -v $(pwd)/output:/app/output \
     --network none \
     pdf-outline-extractor
   ```
3. Find the processed JSON files in the `output` directory

### Command Line Arguments

No command line arguments are needed. The script automatically processes all PDFs in the `/app/input` directory and saves the output to `/app/output`.

## Output Format

For each input PDF file (e.g., `document.pdf`), the tool generates a corresponding JSON file (e.g., `document.json`) with the following structure:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1",
      "page": 1
    },
    {
      "level": "H2",
      "text": "Section 1.1",
      "page": 2
    },
    ...
  ]
}
```

### Output Schema

The output JSON strictly follows this schema:

```json
{
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
```

## Performance

The solution is optimized to process PDFs quickly and efficiently:

- Processes 50+ page PDFs in under 10 seconds
- Uses minimal memory (well under 16GB limit)
- Processes text in batches to handle large documents
- Implements early termination if processing takes too long

## Testing

### Test with Sample Data

1. Place test PDFs in the `input` directory
2. Run the container as described in the Usage section
3. Check the `output` directory for the generated JSON files

### Validation

The output JSON is automatically validated against the schema before being saved. If validation fails, an empty result will be returned.

## Implementation Details

### Algorithm

1. **Text Extraction**: Uses `pdfplumber` to extract text and font information
2. **Font Analysis**: Groups text by line and analyzes font sizes to determine heading hierarchy
3. **Clustering**: Uses a simple binning approach to cluster font sizes into heading levels
4. **Validation**: Validates the output against the required schema

### Dependencies

- Python 3.10
- pdfplumber 0.8.1 (for PDF text extraction)
- jsonschema 4.20.0 (for output validation)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.