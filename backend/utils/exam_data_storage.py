import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import time


class ExamDataStorage:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent / "exam_sync_data_dir"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_device_folder(self, data_type: str, exam_id: str, session_id: str, device_id: str) -> Path:
        folder = self.base_dir / data_type / exam_id / session_id / device_id
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _get_next_file_name(self, folder: Path) -> str:
        timestamp = int(time.time() * 1000)
        counter = 1
        while True:
            filename = f"{timestamp}_{counter}.json"
            if not (folder / filename).exists():
                return filename
            counter += 1

    def _read_json_file(self, file_path: Path) -> Dict:
        if not file_path.exists():
            return {}
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_json_file(self, file_path: Path, data: Dict):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def store_exam_session(self, data: Dict[str, Any]) -> bool:
        exam_id = data.get("examId")
        session_id = data.get("sessionId")
        device_id = data.get("deviceId")

        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        folder = self._get_device_folder("exam_sessions", exam_id, session_id, device_id)
        filename = self._get_next_file_name(folder)
        file_path = folder / filename

        data["received_at"] = datetime.now().isoformat()
        self._write_json_file(file_path, data)
        return True

    def store_question_actions(self, exam_id: str, session_id: str, device_id: str, actions: List[Dict[str, Any]]) -> bool:
        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        folder = self._get_device_folder("question_actions", exam_id, session_id, device_id)
        filename = self._get_next_file_name(folder)
        file_path = folder / filename

        received_at = datetime.now().isoformat()
        for action in actions:
            action["received_at"] = received_at

        self._write_json_file(file_path, {"actions": actions, "received_at": received_at})
        return True

    def store_snapshot_actions(self, exam_id: str, session_id: str, device_id: str, snapshots: List[Dict[str, Any]]) -> bool:
        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        folder = self._get_device_folder("snapshot_actions", exam_id, session_id, device_id)
        filename = self._get_next_file_name(folder)
        file_path = folder / filename

        received_at = datetime.now().isoformat()
        for snapshot in snapshots:
            snapshot["received_at"] = received_at

        self._write_json_file(file_path, {"snapshots": snapshots, "received_at": received_at})
        return True

    def store_final_submission(self, data: Dict[str, Any]) -> bool:
        exam_id = data.get("examId")
        session_id = data.get("sessionId")
        device_id = data.get("deviceId")

        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        folder = self._get_device_folder("final_submissions", exam_id, session_id, device_id)
        filename = self._get_next_file_name(folder)
        file_path = folder / filename

        data["received_at"] = datetime.now().isoformat()
        self._write_json_file(file_path, data)
        return True

    def store_answer_sheet(self, data: Dict[str, Any]) -> bool:
        exam_id = data.get("examId")
        session_id = data.get("sessionId")
        device_id = data.get("deviceId")

        if not all([exam_id, session_id, device_id]):
            raise ValueError("examId, sessionId, and deviceId are required")

        folder = self._get_device_folder("answer_sheets", exam_id, session_id, device_id)
        filename = self._get_next_file_name(folder)
        file_path = folder / filename

        data["received_at"] = datetime.now().isoformat()
        self._write_json_file(file_path, data)
        return True


exam_data_storage = ExamDataStorage()
