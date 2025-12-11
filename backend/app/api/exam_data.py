from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
import logging

from backend.utils.json_storage import JSONStorage

router = APIRouter(prefix="/api/exam-data", tags=["exam-data"])
logger = logging.getLogger(__name__)

exam_sessions_storage = JSONStorage("exam_sessions.json")
question_actions_storage = JSONStorage("question_actions.json")
snapshot_actions_storage = JSONStorage("snapshot_actions.json")
final_submissions_storage = JSONStorage("final_submissions.json")


@router.get("/status")
async def get_sync_server_status():
    return {
        "status": "up",
        "message": "Sync server is up and running",
        "timestamp": datetime.now().isoformat()
    }


class ExamSessionData(BaseModel):
    data: Dict[str, Any]


class QuestionActionData(BaseModel):
    data: Dict[str, Any]


class SnapshotActionData(BaseModel):
    data: Dict[str, Any]


class FinalSubmissionData(BaseModel):
    data: Dict[str, Any]


@router.post("/exam-sessions")
async def receive_exam_session(payload: ExamSessionData):
    try:
        data = payload.data
        data["received_at"] = datetime.now().isoformat()

        sessions = exam_sessions_storage.read()
        if not isinstance(sessions, list):
            sessions = []

        sessions.append(data)
        exam_sessions_storage.write(sessions)

        logger.info(f"Received exam session data: {data}")

        return {
            "status": "success",
            "message": "Exam session data received",
            "timestamp": data["received_at"]
        }
    except Exception as e:
        logger.error(f"Error receiving exam session data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/question-actions")
async def receive_question_action(payload: QuestionActionData):
    try:
        data = payload.data
        data["received_at"] = datetime.now().isoformat()

        actions = question_actions_storage.read()
        if not isinstance(actions, list):
            actions = []

        actions.append(data)
        question_actions_storage.write(actions)

        logger.info(f"Received question action data: {data}")

        return {
            "status": "success",
            "message": "Question action data received",
            "timestamp": data["received_at"]
        }
    except Exception as e:
        logger.error(f"Error receiving question action data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot-actions")
async def receive_snapshot_action(payload: SnapshotActionData):
    try:
        data = payload.data
        data["received_at"] = datetime.now().isoformat()

        snapshots = snapshot_actions_storage.read()
        if not isinstance(snapshots, list):
            snapshots = []

        snapshots.append(data)
        snapshot_actions_storage.write(snapshots)

        logger.info(f"Received snapshot action data: {data}")

        return {
            "status": "success",
            "message": "Snapshot action data received",
            "timestamp": data["received_at"]
        }
    except Exception as e:
        logger.error(f"Error receiving snapshot action data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/final-submissions")
async def receive_final_submission(payload: FinalSubmissionData):
    try:
        data = payload.data
        data["received_at"] = datetime.now().isoformat()

        submissions = final_submissions_storage.read()
        if not isinstance(submissions, list):
            submissions = []

        submissions.append(data)
        final_submissions_storage.write(submissions)

        logger.info(f"Received final submission data: {data}")

        return {
            "status": "success",
            "message": "Final submission data received",
            "timestamp": data["received_at"]
        }
    except Exception as e:
        logger.error(f"Error receiving final submission data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
