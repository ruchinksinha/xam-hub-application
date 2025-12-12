from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

def get_exam_data_dir() -> Path:
    base_dir = Path(__file__).parent.parent.parent.parent / "exam_sync_data_dir"
    return base_dir

@router.get("/sessions")
async def get_exam_sessions():
    base_dir = get_exam_data_dir()
    sessions_dir = base_dir / "exam_sessions"

    if not sessions_dir.exists():
        return {"sessions": []}

    sessions = []

    for exam_id_dir in sessions_dir.iterdir():
        if not exam_id_dir.is_dir():
            continue

        exam_id = exam_id_dir.name

        for session_id_dir in exam_id_dir.iterdir():
            if not session_id_dir.is_dir():
                continue

            session_id = session_id_dir.name
            devices = []

            for device_id_dir in session_id_dir.iterdir():
                if not device_id_dir.is_dir():
                    continue

                device_id = device_id_dir.name
                file_count = len(list(device_id_dir.glob("*.json")))

                devices.append({
                    "deviceId": device_id,
                    "fileCount": file_count
                })

            sessions.append({
                "examId": exam_id,
                "sessionId": session_id,
                "devices": devices,
                "deviceCount": len(devices)
            })

    return {"sessions": sessions}

@router.get("/session/{exam_id}/{session_id}")
async def get_session_details(exam_id: str, session_id: str):
    base_dir = get_exam_data_dir()

    data_types = ["exam_sessions", "question_actions", "snapshot_actions", "final_submissions", "answer_sheets"]

    devices_data = {}

    for data_type in data_types:
        type_dir = base_dir / data_type / exam_id / session_id

        if not type_dir.exists():
            continue

        for device_id_dir in type_dir.iterdir():
            if not device_id_dir.is_dir():
                continue

            device_id = device_id_dir.name

            if device_id not in devices_data:
                devices_data[device_id] = {
                    "deviceId": device_id,
                    "exam_sessions": [],
                    "question_actions": [],
                    "snapshot_actions": [],
                    "final_submissions": [],
                    "answer_sheets": []
                }

            for json_file in sorted(device_id_dir.glob("*.json")):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        data["_filename"] = json_file.name
                        devices_data[device_id][data_type].append(data)
                except Exception:
                    pass

    return {
        "examId": exam_id,
        "sessionId": session_id,
        "devices": list(devices_data.values())
    }

@router.get("/device/{exam_id}/{session_id}/{device_id}")
async def get_device_telemetry(exam_id: str, session_id: str, device_id: str):
    base_dir = get_exam_data_dir()

    data_types = ["exam_sessions", "question_actions", "snapshot_actions", "final_submissions", "answer_sheets"]

    device_data = {
        "deviceId": device_id,
        "examId": exam_id,
        "sessionId": session_id,
        "data": {}
    }

    for data_type in data_types:
        type_dir = base_dir / data_type / exam_id / session_id / device_id

        if not type_dir.exists():
            device_data["data"][data_type] = []
            continue

        files_data = []
        for json_file in sorted(type_dir.glob("*.json")):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    data["_filename"] = json_file.name
                    data["_filepath"] = str(json_file)
                    files_data.append(data)
            except Exception:
                pass

        device_data["data"][data_type] = files_data

    return device_data

@router.get("/stats")
async def get_telemetry_stats():
    base_dir = get_exam_data_dir()

    if not base_dir.exists():
        return {
            "totalExams": 0,
            "totalSessions": 0,
            "totalDevices": 0,
            "dataTypes": {}
        }

    exams = set()
    sessions = set()
    devices = set()
    data_types = {}

    data_type_dirs = ["exam_sessions", "question_actions", "snapshot_actions", "final_submissions", "answer_sheets"]

    for data_type in data_type_dirs:
        type_dir = base_dir / data_type

        if not type_dir.exists():
            data_types[data_type] = 0
            continue

        file_count = 0

        for exam_id_dir in type_dir.iterdir():
            if not exam_id_dir.is_dir():
                continue

            exams.add(exam_id_dir.name)

            for session_id_dir in exam_id_dir.iterdir():
                if not session_id_dir.is_dir():
                    continue

                sessions.add(f"{exam_id_dir.name}/{session_id_dir.name}")

                for device_id_dir in session_id_dir.iterdir():
                    if not device_id_dir.is_dir():
                        continue

                    devices.add(f"{exam_id_dir.name}/{session_id_dir.name}/{device_id_dir.name}")
                    file_count += len(list(device_id_dir.glob("*.json")))

        data_types[data_type] = file_count

    return {
        "totalExams": len(exams),
        "totalSessions": len(sessions),
        "totalDevices": len(devices),
        "dataTypes": data_types
    }
