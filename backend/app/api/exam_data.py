from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime
import logging

from backend.utils.exam_data_storage import exam_data_storage

router = APIRouter(prefix="/api/exam-data", tags=["exam-data"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_sync_server_status():
    return {
        "status": "up",
        "message": "Sync server is up and running",
        "timestamp": datetime.now().isoformat()
    }


class ExamSessionData(BaseModel):
    deviceId: str
    sessionId: str
    examId: str
    studentId: str
    startTime: int
    endTime: Optional[int] = None
    durationSeconds: Optional[int] = None
    isSubmitted: bool = False
    currentQuestionIndex: Optional[int] = None


class QuestionAction(BaseModel):
    id: int
    deviceId: str
    sessionId: str
    examId: str
    questionId: str
    actionType: str
    selectedOption: Optional[str] = None
    timeSpentMs: Optional[int] = None
    timestamp: int


class QuestionActionData(BaseModel):
    actions: List[QuestionAction]


class Snapshot(BaseModel):
    id: int
    deviceId: str
    sessionId: str
    examId: str
    snapshotData: str
    answeredCount: int
    markedCount: int
    notAnsweredCount: int
    notVisitedCount: int
    timestamp: int


class SnapshotActionData(BaseModel):
    snapshots: List[Snapshot]


class FinalSubmissionData(BaseModel):
    id: int
    deviceId: str
    sessionId: str
    examId: str
    submissionData: str
    totalQuestions: int
    answeredCount: int
    markedCount: int
    submissionTime: int


class UserResponse(BaseModel):
    questionId: str
    answered: bool
    markedAnswer: Optional[str] = None
    markedForReview: bool
    visited: bool
    timestamp: str
    timeSpentSeconds: int
    attempt: int


class AnswerSheetData(BaseModel):
    deviceId: str
    sessionId: str
    examId: str
    sessionStartTime: str
    sessionEndTime: str
    sessionDuration: int
    userResponses: List[UserResponse]


@router.post("/exam-sessions")
async def receive_exam_session(payload: ExamSessionData):
    try:
        data = payload.model_dump()
        exam_data_storage.store_exam_session(data)

        logger.info(f"Received exam session data for device: {payload.deviceId}, session: {payload.sessionId}")

        return {
            "status": "success",
            "message": "Exam session data received",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving exam session data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/question-actions")
async def receive_question_action(payload: QuestionActionData):
    try:
        if not payload.actions or len(payload.actions) == 0:
            raise ValueError("actions array cannot be empty")

        first_action = payload.actions[0]
        exam_id = first_action.examId
        session_id = first_action.sessionId
        device_id = first_action.deviceId

        actions_data = [action.model_dump() for action in payload.actions]
        exam_data_storage.store_question_actions(exam_id, session_id, device_id, actions_data)

        logger.info(f"Received {len(payload.actions)} question actions for device: {device_id}, session: {session_id}")

        return {
            "status": "success",
            "message": f"{len(payload.actions)} question actions received",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving question action data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot-actions")
async def receive_snapshot_action(payload: SnapshotActionData):
    try:
        if not payload.snapshots or len(payload.snapshots) == 0:
            raise ValueError("snapshots array cannot be empty")

        first_snapshot = payload.snapshots[0]
        exam_id = first_snapshot.examId
        session_id = first_snapshot.sessionId
        device_id = first_snapshot.deviceId

        snapshots_data = [snapshot.model_dump() for snapshot in payload.snapshots]
        exam_data_storage.store_snapshot_actions(exam_id, session_id, device_id, snapshots_data)

        logger.info(f"Received {len(payload.snapshots)} snapshots for device: {device_id}, session: {session_id}")

        return {
            "status": "success",
            "message": f"{len(payload.snapshots)} snapshots received",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving snapshot action data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/final-submissions")
async def receive_final_submission(payload: FinalSubmissionData):
    try:
        data = payload.model_dump()
        exam_data_storage.store_final_submission(data)

        logger.info(f"Received final submission for device: {payload.deviceId}, session: {payload.sessionId}")

        return {
            "status": "success",
            "message": "Final submission data received",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving final submission data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer-sheet")
async def receive_answer_sheet(payload: AnswerSheetData):
    try:
        data = payload.model_dump()
        exam_data_storage.store_answer_sheet(data)

        logger.info(f"Received answer sheet for device: {payload.deviceId}, session: {payload.sessionId}, exam: {payload.examId}")

        return {
            "status": "success",
            "message": "Answer sheet data received",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving answer sheet data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
