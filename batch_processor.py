"""
Batch audio file processing for transcription.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from openai import OpenAI

import transcriber

# Batch jobs directory
BATCH_JOBS_DIR = Path("data/batch_jobs")
SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def initialize_storage() -> None:
    """Initialize batch storage directory."""
    BATCH_JOBS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_component(value: str) -> str:
    """Convert user-provided names to safe path components."""
    cleaned = SAFE_NAME_PATTERN.sub("_", value).strip("._")
    return cleaned or "batch"


def create_batch_job(username: str, file_paths: List[str], job_name: str = "Batch Job") -> str:
    """
    Create a new batch processing job.

    Args:
        username (str): Username.
        file_paths (List[str]): List of audio file paths to process.
        job_name (str): Name of the batch job.

    Returns:
        str: Batch job ID.
    """
    initialize_storage()

    safe_username = _safe_component(username)
    job_id = f"{safe_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    job_data = {
        "job_id": job_id,
        "username": username,
        "job_name": job_name,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "files": [{"path": fp, "status": "pending"} for fp in file_paths],
        "progress": 0,
        "results": [],
    }

    job_file = BATCH_JOBS_DIR / f"{job_id}.json"
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job_data, f, indent=2)

    return job_id


def get_batch_job(job_id: str) -> Optional[Dict]:
    """
    Get batch job details.

    Args:
        job_id (str): Batch job ID.

    Returns:
        Dict or None: Job data if found, None otherwise.
    """
    initialize_storage()

    job_file = BATCH_JOBS_DIR / f"{job_id}.json"

    if not job_file.exists():
        return None

    with open(job_file, "r", encoding="utf-8") as f:
        return json.load(f)


def update_batch_job(job_id: str, updates: Dict) -> bool:
    """
    Update batch job.

    Args:
        job_id (str): Batch job ID.
        updates (Dict): Fields to update.

    Returns:
        bool: True if updated, False if job not found.
    """
    job = get_batch_job(job_id)

    if not job:
        return False

    job.update(updates)

    job_file = BATCH_JOBS_DIR / f"{job_id}.json"
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

    return True


def process_batch_job(
    job_id: str, client: OpenAI, progress_callback: Optional[Callable] = None
) -> bool:
    """
    Process a batch job.

    Args:
        job_id (str): Batch job ID.
        client (OpenAI): Initialized OpenAI client.
        progress_callback (Callable, optional): Progress callback function.

    Returns:
        bool: True if successful, False otherwise.
    """
    job = get_batch_job(job_id)

    if not job:
        return False

    update_batch_job(job_id, {"status": "processing"})

    results = []
    total_files = len(job["files"])
    if total_files == 0:
        update_batch_job(job_id, {"status": "completed", "progress": 100, "results": []})
        return True

    for idx, file_data in enumerate(job["files"]):
        file_path = file_data["path"]

        try:
            # Update job with current file being processed
            job["files"][idx]["status"] = "processing"
            update_batch_job(job_id, {"files": job["files"]})

            # Transcribe
            text = transcriber.transcribe_audio(file_path, client)

            # Mark as complete
            job["files"][idx]["status"] = "completed"
            results.append(
                {
                    "file": file_path,
                    "status": "completed",
                    "text": text,
                    "processed_at": datetime.now().isoformat(),
                }
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            job["files"][idx]["status"] = "failed"
            results.append(
                {
                    "file": file_path,
                    "status": "failed",
                    "error": str(e),
                    "processed_at": datetime.now().isoformat(),
                }
            )

        # Update progress
        progress = (idx + 1) / total_files
        update_batch_job(
            job_id,
            {
                "files": job["files"],
                "progress": round(progress * 100, 2),
                "results": results,
            },
        )

        if progress_callback:
            progress_callback(progress)

    final_status = (
        "failed" if any(result["status"] == "failed" for result in results) else "completed"
    )
    update_batch_job(job_id, {"status": final_status})

    return True


def get_user_batch_jobs(username: str) -> List[Dict]:
    """
    Get all batch jobs for a user.

    Args:
        username (str): Username.

    Returns:
        List[Dict]: List of batch job summaries.
    """
    initialize_storage()

    batch_files = BATCH_JOBS_DIR.glob(f"{_safe_component(username)}_*.json")
    jobs = []

    for batch_file in sorted(batch_files, reverse=True):
        with open(batch_file, "r", encoding="utf-8") as f:
            job = json.load(f)
            jobs.append(
                {
                    "job_id": job["job_id"],
                    "job_name": job["job_name"],
                    "created_at": job["created_at"],
                    "status": job["status"],
                    "progress": job["progress"],
                    "file_count": len(job["files"]),
                    "completed_count": sum(1 for f in job["files"] if f["status"] == "completed"),
                }
            )

    return jobs


def delete_batch_job(job_id: str) -> bool:
    """
    Delete batch job.

    Args:
        job_id (str): Batch job ID.

    Returns:
        bool: True if deleted, False if not found.
    """
    job_file = BATCH_JOBS_DIR / f"{job_id}.json"

    if not job_file.exists():
        return False

    job_file.unlink()
    return True


def get_batch_results(job_id: str) -> Optional[List[Dict]]:
    """
    Get batch job results.

    Args:
        job_id (str): Batch job ID.

    Returns:
        List[Dict] or None: Results if found, None otherwise.
    """
    job = get_batch_job(job_id)

    if not job:
        return None

    return job.get("results", [])
