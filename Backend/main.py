from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
import pandas as pd
import io
import csv
import re
from datetime import datetime
import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import base64

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Agentic Web App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_csv_delimiter(content):
    try:
        sample = content[:1024].decode('utf-8')
        return csv.Sniffer().sniff(sample).delimiter
    except Exception:
        logger.warning("Failed to detect delimiter; defaulting to comma")
        return ','

@app.get("/")
async def root():
    return {"message": "Smart Agentic Web App API is running", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    combined_df = pd.DataFrame()
    processed_files = []
    errors = []

    for i, file in enumerate(files):
        try:
            logger.info(f"Receiving file {i+1}: {file.filename}")
            content = await file.read()
            if not content:
                errors.append(f"{file.filename} is empty")
                continue

            if file.filename.endswith(".csv"):
                delimiter = detect_csv_delimiter(content)
                try:
                    df = pd.read_csv(io.BytesIO(content), delimiter=delimiter, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(content), delimiter=delimiter, encoding="latin1")
            else:
                df = pd.read_excel(io.BytesIO(content))

            if df.empty:
                errors.append(f"{file.filename} has no data")
                continue

            # Clean data
            original_rows, original_cols = df.shape
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            df.columns = df.columns.str.strip().str.replace('\t', ' ').str.replace('\n', ' ')

            # Optional: fix numeric values using commas
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                    try:
                        df[col] = df[col].astype(float)
                    except:
                        continue

            cleaned_rows, cleaned_cols = df.shape
            if cleaned_rows == 0:
                errors.append(f"{file.filename}: All rows removed after cleaning")
                continue

            df["source_file"] = file.filename
            df["processed_at"] = datetime.now().isoformat()
            combined_df = pd.concat([combined_df, df], ignore_index=True)

            processed_files.append({
                "filename": file.filename,
                "original_rows": original_rows,
                "cleaned_rows": cleaned_rows,
                "original_columns": original_cols,
                "cleaned_columns": cleaned_cols,
                "removed_rows": original_rows - cleaned_rows,
                "removed_columns": original_cols - cleaned_cols,
                "columns": df.columns.tolist()
            })

        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            errors.append(f"{file.filename}: {str(e)}")
            continue

    response = {
        "total_files_received": len(files),
        "files_processed": len(processed_files),
        "files_with_errors": len(errors),
        "processed_files": processed_files,
        "errors": errors
    }

    if not combined_df.empty:
        response["preview"] = combined_df.head(10).to_dict(orient="records")
        response["columns"] = combined_df.columns.tolist()
        response["data_types"] = combined_df.dtypes.astype(str).to_dict()
        response["summary"] = {
            "total_rows": len(combined_df),
            "total_columns": len(combined_df.columns),
            "memory_usage": f"{combined_df.memory_usage(deep=True).sum() / (1024):.2f} KB"
        }
    else:
        response["preview"] = []
        response["columns"] = []
        response["data_types"] = {}
        response["summary"] = {}

    logger.info("Upload processing complete.")
    return response

# Command input model
class CommandRequest(BaseModel):
    command: str
    preview: List[dict]

@app.post("/command")
async def run_command(request: CommandRequest):
    command = request.command.strip().lower()
    df = pd.DataFrame(request.preview)

    if df.empty:
        return {"error": "No data available to process the command."}

    # Match "show 5 rows", "get 10", "15 rows", etc.
    match = re.match(r"(show|get)?\s*(\d+)\s*(rows)?", command)
    if match:
        n = int(match.group(2))
        result = df.head(n).to_dict(orient="records")
        return {"result": result}

    # Plot top N <Column>
    plot_top_match = re.match(r"plot top (\d+) (.+)", command)
    if plot_top_match:
        n = int(plot_top_match.group(1))
        col = plot_top_match.group(2).strip()
        if col in df.columns:
            # Create matplotlib plot
            plt.figure(figsize=(10, 6))
            counts = df[col].value_counts().head(n)
            plt.bar(range(len(counts)), counts.values, color='#6366f1')
            plt.xticks(range(len(counts)), counts.index, rotation=45, ha='right')
            plt.title(f'Top {n} {col}')
            plt.xlabel(col)
            plt.ylabel('Count')
            plt.tight_layout()
            
            # Save plot to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Convert to base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            return {
                "plot_image": f"data:image/png;base64,{img_base64}",
                "plot_type": "bar",
                "title": f"Top {n} {col}"
            }
        else:
            return {"error": f"Column '{col}' not found for plotting."}

    # Heatmap <Col1> <Col2>
    heatmap_match = re.match(r"heatmap (\w+) (\w+)", command)
    if heatmap_match:
        col1 = heatmap_match.group(1)
        col2 = heatmap_match.group(2)
        if col1 in df.columns and col2 in df.columns:
            # Create heatmap using matplotlib
            plt.figure(figsize=(10, 8))
            
            # Create pivot table for heatmap
            heatmap_data = df.groupby([col1, col2]).size().unstack(fill_value=0)
            
            plt.imshow(heatmap_data.values, cmap='viridis', aspect='auto')
            plt.colorbar(label='Count')
            plt.title(f'Heatmap: {col1} vs {col2}')
            plt.xlabel(col1)
            plt.ylabel(col2)
            
            # Set tick labels
            if len(heatmap_data.columns) <= 20:  # Only show labels if not too many
                plt.xticks(range(len(heatmap_data.columns)), heatmap_data.columns, rotation=45, ha='right')
            if len(heatmap_data.index) <= 20:
                plt.yticks(range(len(heatmap_data.index)), heatmap_data.index)
            
            plt.tight_layout()
            
            # Save plot to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Convert to base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            return {
                "plot_image": f"data:image/png;base64,{img_base64}",
                "plot_type": "heatmap",
                "title": f"Heatmap: {col1} vs {col2}"
            }
        else:
            return {"error": f"One or both columns '{col1}', '{col2}' not found for heatmap."}

    elif "columns" in command:
        return {
            "summary": {
                "columns": df.columns.tolist(),
                "shape": df.shape
            }
        }

    elif "shape" in command or "size" in command:
        return {
            "summary": {
                "columns": df.columns.tolist(),
                "shape": df.shape
            }
        }

    else:
        return {"error": "Unknown command"}
