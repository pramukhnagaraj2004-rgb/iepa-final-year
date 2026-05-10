import os
import sys
import json
import uuid
import subprocess
from pathlib import Path

# Add project root to sys.path to import iepa modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from iepa.backend.ml.mapper.weak_labeler import WeakLabeler
from iepa.backend.parser.error_normalizer import ErrorNormalizer

def run_python_code(file_path):
    """
    Executes a Python file and captures its stderr.
    """
    try:
        # Run the script with a timeout to avoid infinite loops blocking the pipeline
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stderr
    except subprocess.TimeoutExpired as e:
        return f"TimeoutError: {e}"
    except Exception as e:
        return str(e)

def process_dataset(dataset_path, output_json_path, source_name="deepfix"):
    print(f"[*] Scanning {dataset_path} for .py files...")
    
    labeler = WeakLabeler()
    normalizer = ErrorNormalizer()
    
    labeled_dataset = []
    
    # Recursively find all .py files
    py_files = list(Path(dataset_path).rglob("*.py"))
    
    if not py_files:
        print(f"[-] No .py files found in {dataset_path}")
    
    for filepath in py_files:
        print(f"  -> Processing {filepath.name}...")
        
        # Read the raw source code
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Execute to capture raw error
        raw_error = run_python_code(str(filepath))
        
        # Skip files that don't produce an error (if we only want buggy programs)
        if not raw_error.strip():
            print(f"     [SKIP] No error produced by {filepath.name}")
            continue
            
        # Normalize the error
        normalized_events = normalizer.normalize(raw_error, language="python")
        
        # Map to concept
        # We use the raw error string for the weak labeler as defined in weak_labeler.py
        concept_label = labeler.map_error_to_concept(raw_error)
        
        # Determine confidence
        confidence = "low" if concept_label == "unknown" else "high"
        
        # Create dataset entry
        entry = {
            "id": str(uuid.uuid4()),
            "source": source_name,
            "language": "python",
            "code": code,
            "error_raw": raw_error,
            "error_normalized": normalized_events,
            "concept_label": concept_label,
            "confidence": confidence
        }
        
        labeled_dataset.append(entry)
        
    # Save the unified dataset
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(labeled_dataset, f, indent=2)
        
    print(f"[+] Successfully saved {len(labeled_dataset)} labeled events to {output_json_path}")

if __name__ == "__main__":
    PROJECT_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    DATA_DIR = PROJECT_ROOT / "data"
    SYNTHETIC_DIR = DATA_DIR / "synthetic" / "python"
    OUTPUT_JSON = DATA_DIR / "labeled_dataset.json"
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    
    process_dataset(SYNTHETIC_DIR, OUTPUT_JSON, source_name="synthetic")
