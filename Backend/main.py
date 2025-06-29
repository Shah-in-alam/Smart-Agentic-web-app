from fastapi import FastAPI, File, UploadFile, HTTPException, Body
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
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Agentic Web App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
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

    # Validate number of files
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed")

    # Validate total file size (50MB limit)
    total_size = 0
    for file in files:
        content = await file.read()
        total_size += len(content)
        file.file.seek(0)  # Reset file pointer for later reading
    
    if total_size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="Total file size exceeds 50MB limit")

    logger.info(f"Starting upload processing for {len(files)} files (total size: {total_size / (1024*1024):.2f} MB)")
    individual_dfs = []
    processed_files = []
    errors = []
    file_names = []
    
    for i, file in enumerate(files):
        try:
            logger.info(f"Processing file {i+1}/{len(files)}: {file.filename}")
            content = await file.read()
            if not content:
                errors.append(f"{file.filename} is empty")
                continue

            logger.info(f"Reading file {file.filename} with size {len(content)} bytes")
            
            if file.filename.endswith(".csv"):
                delimiter = detect_csv_delimiter(content)
                try:
                    df = pd.read_csv(io.BytesIO(content), delimiter=delimiter, encoding="utf-8")
                except UnicodeDecodeError:
                    logger.info(f"Trying latin1 encoding for {file.filename}")
                    df = pd.read_csv(io.BytesIO(content), delimiter=delimiter, encoding="latin1")
            else:
                df = pd.read_excel(io.BytesIO(content))

            logger.info(f"Successfully read {file.filename}: {df.shape[0]} rows, {df.shape[1]} columns")

            if df.empty:
                errors.append(f"{file.filename} has no data")
                continue

            # Clean data
            original_rows, original_cols = df.shape
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            df.columns = df.columns.str.strip().str.replace('\t', ' ').str.replace('\n', ' ')

            # Optimized numeric conversion - only process first few columns to avoid hanging
            logger.info(f"Processing {len(df.columns)} columns for {file.filename}")
            for col in df.columns[:10]:  # Limit to first 10 columns to prevent hanging
                if df[col].dtype == object and len(df[col].dropna()) > 0:
                    try:
                        # Sample first 100 values to check if conversion is possible
                        sample_values = df[col].dropna().head(100)
                        if sample_values.astype(str).str.replace(',', '.').str.replace('.', '').str.isdigit().all():
                            df[col] = df[col].astype(str).str.replace(',', '.')
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    except Exception as e:
                        logger.warning(f"Could not convert column {col} to numeric: {str(e)}")
                        continue

            cleaned_rows, cleaned_cols = df.shape
            if cleaned_rows == 0:
                errors.append(f"{file.filename}: All rows removed after cleaning")
                continue

            # Add source_file column
            df["source_file"] = file.filename

            # Store individual dataframe for joining
            individual_dfs.append(df)
            file_names.append(file.filename)

            processed_files.append({
                "filename": file.filename,
                "original_rows": original_rows,
                "cleaned_rows": cleaned_rows,
                "original_columns": original_cols,
                "cleaned_columns": cleaned_cols,
                "removed_rows": original_rows - cleaned_rows,
                "removed_columns": original_cols - cleaned_cols,
                "columns": df.columns.tolist(),
                "file_size": len(content)
            })

        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            errors.append(f"{file.filename}: {str(e)}")
            continue

    # Smart join all dataframes
    join_info = {}
    if len(individual_dfs) > 1:
        logger.info("Attempting smart join of multiple files")
        join_candidates = detect_join_keys(individual_dfs)
        join_info = {
            "join_candidates": join_candidates,
            "join_strategy": "smart_join" if join_candidates else "concatenate"
        }
        
        if join_candidates:
            best_key = max(join_candidates.keys(), key=lambda k: len(join_candidates[k]))
            join_info["best_join_key"] = best_key
            join_info["files_joined"] = len(join_candidates[best_key])
            logger.info(f"Smart join using key: {best_key}")
        else:
            logger.info("No common ID columns found, concatenating files")
    
    combined_df = smart_join_dataframes(individual_dfs, file_names)
    combined_df["processed_at"] = datetime.now().isoformat()

    response = {
        "total_files_received": len(files),
        "files_processed": len(processed_files),
        "files_with_errors": len(errors),
        "total_size_mb": f"{total_size / (1024*1024):.2f}",
        "processed_files": processed_files,
        "errors": errors,
        "join_info": join_info
    }

    if not combined_df.empty:
        # Robustly replace inf, -inf, and NaN with None for JSON serialization
        combined_df = combined_df.applymap(lambda x: None if pd.isnull(x) or x in [np.inf, -np.inf] else x)
        if 'source_file' in combined_df.columns:
            combined_df = combined_df.drop(columns=['source_file'])
        response["preview"] = combined_df.head(10).to_dict(orient="records")
        response["columns"] = combined_df.columns.tolist()
        response["data_types"] = combined_df.dtypes.astype(str).to_dict()
        response["summary"] = {
            "total_rows": len(combined_df),
            "total_columns": len(combined_df.columns),
            "memory_usage": f"{combined_df.memory_usage(deep=True).sum() / (1024):.2f} KB",
            "source_files": []
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
    
    logger.info(f"Received command: '{command}'")
    logger.info(f"DataFrame shape: {df.shape}")
    logger.info(f"Available columns: {df.columns.tolist()}")

    if df.empty:
        return {"error": "No data available to process the command."}

    # Create case-insensitive column mapping
    column_mapping = {col.lower(): col for col in df.columns}
    logger.info(f"Column mapping: {column_mapping}")

    # Match "show 5 rows", "get 10", "15 rows", etc.
    match = re.match(r"(show|get)?\s*(\d+)\s*(rows)?", command)
    if match:
        n = int(match.group(2))
        result = df.head(n).to_dict(orient="records")
        return {"result": result}

    # Plot top N <Column> - more flexible pattern
    plot_patterns = [
        r"plot top (\d+) (.+)",
        r"plot (\d+) (.+)",
        r"top (\d+) (.+) plot"
    ]
    
    for pattern in plot_patterns:
        plot_match = re.match(pattern, command)
        if plot_match:
            n = int(plot_match.group(1))
            col_lower = plot_match.group(2).strip().lower()
            logger.info(f"Plot command matched: n={n}, col_lower='{col_lower}'")
            
            if col_lower in column_mapping:
                col = column_mapping[col_lower]  # Get the original column name
                logger.info(f"Found column: '{col}' for '{col_lower}'")
                try:
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
                    
                    logger.info(f"Successfully created plot for column '{col}'")
                    return {
                        "plot_image": f"data:image/png;base64,{img_base64}",
                        "plot_type": "bar",
                        "title": f"Top {n} {col}"
                    }
                except Exception as e:
                    logger.error(f"Error creating plot: {str(e)}")
                    return {"error": f"Error creating plot: {str(e)}"}
            else:
                logger.warning(f"Column '{col_lower}' not found. Available columns: {list(column_mapping.keys())}")
                return {"error": f"Column '{col_lower}' not found. Available columns: {list(column_mapping.keys())}"}

    # Heatmap <Col1> <Col2> - more flexible pattern
    heatmap_patterns = [
        r"heatmap (\w+) (\w+)",
        r"heatmap (.+) (.+)",
        r"(.+) (.+) heatmap"
    ]
    
    for pattern in heatmap_patterns:
        heatmap_match = re.match(pattern, command)
        if heatmap_match:
            col1_lower = heatmap_match.group(1).strip().lower()
            col2_lower = heatmap_match.group(2).strip().lower()
            logger.info(f"Heatmap command matched: col1_lower='{col1_lower}', col2_lower='{col2_lower}'")
            
            if col1_lower in column_mapping and col2_lower in column_mapping:
                col1 = column_mapping[col1_lower]  # Get the original column name
                col2 = column_mapping[col2_lower]  # Get the original column name
                logger.info(f"Found columns: '{col1}' and '{col2}'")
                try:
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
                    
                    logger.info(f"Successfully created heatmap for columns '{col1}' and '{col2}'")
                    return {
                        "plot_image": f"data:image/png;base64,{img_base64}",
                        "plot_type": "heatmap",
                        "title": f"Heatmap: {col1} vs {col2}"
                    }
                except Exception as e:
                    logger.error(f"Error creating heatmap: {str(e)}")
                    return {"error": f"Error creating heatmap: {str(e)}"}
            else:
                missing_cols = []
                if col1_lower not in column_mapping:
                    missing_cols.append(col1_lower)
                if col2_lower not in column_mapping:
                    missing_cols.append(col2_lower)
                logger.warning(f"Columns {missing_cols} not found. Available columns: {list(column_mapping.keys())}")
                return {"error": f"Columns {missing_cols} not found. Available columns: {list(column_mapping.keys())}"}

    # Check for other commands
    if "columns" in command:
        return {
            "summary": {
                "columns": df.columns.tolist(),
                "shape": df.shape
            }
        }
    
    if "shape" in command or "size" in command:
        return {
            "summary": {
                "columns": df.columns.tolist(),
                "shape": df.shape
            }
        }
    
    # New command: show files summary
    if "files summary" in command or "file summary" in command:
        if "source_file" in df.columns:
            file_summary = df.groupby("source_file").agg({
                "source_file": "count"
            }).rename(columns={"source_file": "rows"}).to_dict("index")
            
            return {
                "files_summary": {
                    "total_files": len(file_summary),
                    "files": file_summary,
                    "total_rows": len(df)
                }
            }
        else:
            return {"error": "No file source information available"}
    
    # New command: show join info
    if "join info" in command or "join details" in command:
        # This will be handled by the frontend using the join_info from upload response
        return {"message": "Join information is available in the upload response"}
    
    # New command: analyze joins
    if "analyze joins" in command or "join analysis" in command:
        if "source_file" in df.columns:
            # Analyze the joined data
            file_analysis = {}
            for file_name in df["source_file"].unique():
                file_data = df[df["source_file"] == file_name]
                file_analysis[file_name] = {
                    "rows": len(file_data),
                    "columns": len(file_data.columns),
                    "unique_values": {}
                }
                
                # Count unique values in key columns
                for col in file_data.columns:
                    if col != "source_file" and col != "processed_at":
                        unique_count = file_data[col].nunique()
                        file_analysis[file_name]["unique_values"][col] = unique_count
            
            return {
                "join_analysis": {
                    "total_files": len(file_analysis),
                    "total_rows": len(df),
                    "file_analysis": file_analysis,
                    "join_columns": [col for col in df.columns if any(keyword in col.lower() for keyword in ['id', 'code', 'key', 'ref'])]
                }
            }
        else:
            return {"error": "No file source information available"}
    
    logger.warning(f"Unknown command: '{command}'")
    return {"error": f"Unknown command: '{command}'. Try: 'show 5 rows', 'plot top 10 ColumnName', 'heatmap Col1 Col2', 'show files summary', 'join info', or 'analyze joins'"}

def detect_join_keys(dfs):
    """Detect potential join keys across multiple dataframes, prioritizing 'id' columns"""
    join_candidates = {}
    all_columns = set()
    for df in dfs:
        all_columns.update(df.columns)
    # Prioritize 'id' columns
    id_like_columns = [col for col in all_columns if 'id' in col.lower()]
    prioritized_columns = id_like_columns + [col for col in all_columns if col not in id_like_columns]
    for col in prioritized_columns:
        present_in = [i for i, df in enumerate(dfs) if col in df.columns]
        if len(present_in) > 1:
            join_candidates[col] = present_in
    return join_candidates

def smart_join_dataframes(dfs, file_names):
    """Intelligently join multiple dataframes based on common ID columns using robust inner joins"""
    if len(dfs) <= 1:
        return dfs[0] if dfs else pd.DataFrame()
    logger.info(f"Attempting to join {len(dfs)} dataframes")
    join_candidates = detect_join_keys(dfs)
    logger.info(f"Found join candidates: {join_candidates}")
    if not join_candidates:
        logger.info("No common ID columns found, concatenating vertically")
        combined_df = pd.concat(dfs, ignore_index=True)
        return combined_df
    # Pick the id-like join key with the most files
    best_join_key = None
    max_common_files = 0
    for col, file_indices in join_candidates.items():
        if len(file_indices) > max_common_files:
            max_common_files = len(file_indices)
            best_join_key = col
    if best_join_key:
        logger.info(f"Using '{best_join_key}' as join key (inner join)")
        files_with_key = join_candidates[best_join_key]
        result_df = dfs[files_with_key[0]].copy()
        for i in files_with_key[1:]:
            df_to_join = dfs[i].copy()
            result_df = result_df.merge(
                df_to_join,
                on=best_join_key,
                how='inner',
                suffixes=('', f'_{file_names[i].split(".")[0]}')
            )
            logger.info(f"Inner joined with {file_names[i]}, result shape: {result_df.shape}")
        # Add dataframes that don't have the join key (concatenate)
        remaining_files = [i for i in range(len(dfs)) if i not in files_with_key]
        if remaining_files:
            logger.info(f"Concatenating {len(remaining_files)} files without join key")
            remaining_dfs = [dfs[i].copy() for i in remaining_files]
            remaining_combined = pd.concat(remaining_dfs, ignore_index=True)
            result_df = pd.concat([result_df, remaining_combined], ignore_index=True)
        return result_df
    logger.info("No suitable join key found, concatenating vertically")
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df

# Regression endpoint
@app.post("/regression")
async def regression(
    data: dict = Body(...),
    target: str = Body(...),
    features: list = Body(...)
):
    df = pd.DataFrame(data)
    # Drop rows with missing values in features or target
    df = df.dropna(subset=features + [target])
    X = df[features]
    y = df[target]
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    return {
        "r2": r2,
        "mse": mse,
        "coefficients": dict(zip(features, model.coef_)),
        "intercept": model.intercept_,
        "predictions": y_pred.tolist()
    }
