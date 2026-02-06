"""
Endpoints to manage announcements
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson.objectid import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def _require_teacher(username: Optional[str]):
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    return teacher


@router.get("", response_model=List[Dict[str, Any]])
def get_active_announcements():
    """Return active announcements (started and not yet expired). Public endpoint."""
    now = datetime.utcnow()
    query = {
        "expires_at": {"$gt": now},
        "$or": [
            {"starts_at": {"$lte": now}},
            {"starts_at": None},
            {"starts_at": {"$exists": False}},
        ],
    }
    results = []
    for doc in announcements_collection.find(query).sort("expires_at", 1):
        results.append({
            "id": str(doc.get("_id")),
            "message": doc.get("message"),
            "starts_at": doc.get("starts_at"),
            "expires_at": doc.get("expires_at"),
            "created_by": doc.get("created_by"),
        })
    return results


@router.get("/all", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = None):
    """Return all announcements (admin/teacher only)"""
    _require_teacher(teacher_username)
    results = []
    for doc in announcements_collection.find().sort("expires_at", 1):
        results.append({
            "id": str(doc.get("_id")),
            "message": doc.get("message"),
            "starts_at": doc.get("starts_at"),
            "expires_at": doc.get("expires_at"),
            "created_by": doc.get("created_by"),
        })
    return results


@router.post("", response_model=Dict[str, Any])
def create_announcement(message: str, expires_at: str, starts_at: Optional[str] = None, teacher_username: Optional[str] = None):
    """Create an announcement (teacher only). `expires_at` required (ISO format), `starts_at` optional."""
    teacher = _require_teacher(teacher_username)

    if not message or not expires_at:
        raise HTTPException(status_code=400, detail="Message and expires_at are required")

    try:
        expires_dt = datetime.fromisoformat(expires_at)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid expires_at format. Use ISO datetime format (e.g. YYYY-MM-DDTHH:MM)")

    starts_dt = None
    if starts_at:
        try:
            starts_dt = datetime.fromisoformat(starts_at)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid starts_at format. Use ISO datetime format (e.g. YYYY-MM-DDTHH:MM)")

    doc = {
        "message": message,
        "starts_at": starts_dt,
        "expires_at": expires_dt,
        "created_by": teacher.get("username", teacher.get("_id")),
        "created_at": datetime.utcnow(),
    }

    result = announcements_collection.insert_one(doc)
    return {"id": str(result.inserted_id), "message": message}


@router.put("/{ann_id}", response_model=Dict[str, Any])
def update_announcement(ann_id: str, message: Optional[str] = None, expires_at: Optional[str] = None, starts_at: Optional[str] = None, teacher_username: Optional[str] = None):
    """Update an announcement (teacher only)"""
    _require_teacher(teacher_username)

    try:
        oid = ObjectId(ann_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    update = {}
    if message is not None:
        update["message"] = message
    if expires_at is not None:
        try:
            update["expires_at"] = datetime.fromisoformat(expires_at)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid expires_at format")
    if starts_at is not None:
        if starts_at == "":
            update["starts_at"] = None
        else:
            try:
                update["starts_at"] = datetime.fromisoformat(starts_at)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid starts_at format")

    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = announcements_collection.update_one({"_id": oid}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"id": ann_id, "updated": True}


@router.delete("/{ann_id}")
def delete_announcement(ann_id: str, teacher_username: Optional[str] = None):
    """Delete an announcement (teacher only)"""
    _require_teacher(teacher_username)

    try:
        oid = ObjectId(ann_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    result = announcements_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"id": ann_id, "deleted": True}
