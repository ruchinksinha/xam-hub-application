import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class ExamDataStorage:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "data" / "exam_data"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_device_folder(self, exam_id: str, session_id: str, device_id: str) -> Path:
        folder = self.base_dir / exam_id / session_id / device_id
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _get_file_path(self, exam_id: str, session_id: str, device_id: str, filename: str) -> Path:
        folder = self._get_device_folder(exam_id, session_id, device_id)
        return folder / filename

    def _read_json_file(self, file_path: Path) -> List[Dict]:
        if not file_path.exists():
            return []
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_json_file(self, file_path: Path, data: List[Dict]):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def store_exam_session(self, data: Dict[str, Any]) -> bool:
        exam_id = data.get("examId")
        session_id = data.get("sessionId")
        device_id = data.get("deviceId")

        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        file_path = self._get_file_path(exam_id, session_id, device_id, "exam_sessions.json")
        sessions = self._read_json_file(file_path)

        data["received_at"] = datetime.now().isoformat()
        sessions.append(data)

        self._write_json_file(file_path, sessions)
        return True

    def store_question_actions(self, exam_id: str, session_id: str, device_id: str, actions: List[Dict[str, Any]]) -> bool:
        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        file_path = self._get_file_path(exam_id, session_id, device_id, "question_actions.json")
        existing_actions = self._read_json_file(file_path)

        for action in actions:
            action["received_at"] = datetime.now().isoformat()

        existing_actions.extend(actions)
        self._write_json_file(file_path, existing_actions)
        return True

    def store_snapshot_actions(self, exam_id: str, session_id: str, device_id: str, snapshots: List[Dict[str, Any]]) -> bool:
        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        file_path = self._get_file_path(exam_id, session_id, device_id, "snapshot_actions.json")
        existing_snapshots = self._read_json_file(file_path)

        for snapshot in snapshots:
            snapshot["received_at"] = datetime.now().isoformat()

        existing_snapshots.extend(snapshots)
        self._write_json_file(file_path, existing_snapshots)
        return True

    def store_final_submission(self, data: Dict[str, Any]) -> bool:
        exam_id = data.get("examId")
        session_id = data.get("sessionId")
        device_id = data.get("deviceId")

        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        file_path = self._get_file_path(exam_id, session_id, device_id, "final_submissions.json")
        submissions = self._read_json_file(file_path)

        data["received_at"] = datetime.now().isoformat()
        submissions.append(data)

        self._write_json_file(file_path, submissions)
        return True


exam_data_storage = ExamDataStorage()
