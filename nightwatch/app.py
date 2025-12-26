from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from nightwatch.db import get_db, init_db
from nightwatch.models import Shift, Task
from nightwatch.schemas import (
    ShiftNotesIn,
    ShiftOut,
    ShiftStartOut,
    SystemOut,
    TaskIn,
    TaskOut,
)
from nightwatch.system_watch import read_system_snapshot


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _shift_out(s: Shift) -> ShiftOut:
    return ShiftOut(id=s.id, started_at=s.started_at, ended_at=s.ended_at, notes=s.notes)


def _task_out(t: Task) -> TaskOut:
    return TaskOut(
        id=t.id,
        title=t.title,
        created_at=t.created_at,
        completed_at=t.completed_at,
        shift_id=t.shift_id,
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Nightwatch OS Dashboard", version="0.1.0")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def index() -> Response:
        return FileResponse(static_dir / "index.html")

    @app.get("/favicon.ico")
    def favicon() -> Response:
        # Avoid noisy 404s; no icon in MVP.
        return Response(status_code=204)

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/shift/current", response_model=ShiftOut | None)
    def shift_current(db: Session = Depends(get_db)) -> ShiftOut | None:
        s = db.execute(select(Shift).where(Shift.ended_at.is_(None)).order_by(Shift.id.desc())).scalars().first()
        return _shift_out(s) if s else None

    @app.post("/api/shift/start", response_model=ShiftStartOut)
    def shift_start(db: Session = Depends(get_db)) -> ShiftStartOut:
        active = (
            db.execute(select(Shift).where(Shift.ended_at.is_(None)).order_by(Shift.id.desc()))
            .scalars()
            .first()
        )
        if active:
            return ShiftStartOut(shift=_shift_out(active), carried_task_count=0, already_active=True)

        new_shift = Shift(started_at=_utcnow(), ended_at=None, notes="")
        db.add(new_shift)
        db.flush()  # assigns id

        # Carry unfinished tasks forward (including "unassigned" tasks created before a shift started).
        carried = db.execute(
            update(Task)
            .where(Task.completed_at.is_(None))
            .values(shift_id=new_shift.id)
            .execution_options(synchronize_session="fetch")
        )

        db.commit()
        db.refresh(new_shift)
        return ShiftStartOut(
            shift=_shift_out(new_shift),
            carried_task_count=int(getattr(carried, "rowcount", 0) or 0),
            already_active=False,
        )

    @app.post("/api/shift/end", response_model=ShiftOut)
    def shift_end(db: Session = Depends(get_db)) -> ShiftOut:
        active = (
            db.execute(select(Shift).where(Shift.ended_at.is_(None)).order_by(Shift.id.desc()))
            .scalars()
            .first()
        )
        if not active:
            raise HTTPException(status_code=409, detail="No active shift.")
        active.ended_at = _utcnow()
        db.add(active)
        db.commit()
        db.refresh(active)
        return _shift_out(active)

    @app.put("/api/shift/{shift_id}/notes", response_model=ShiftOut)
    def shift_notes(shift_id: int, payload: ShiftNotesIn, db: Session = Depends(get_db)) -> ShiftOut:
        s = db.get(Shift, shift_id)
        if not s:
            raise HTTPException(status_code=404, detail="Shift not found.")
        s.notes = payload.notes
        db.add(s)
        db.commit()
        db.refresh(s)
        return _shift_out(s)

    @app.get("/api/tasks/current", response_model=list[TaskOut])
    def tasks_current(db: Session = Depends(get_db)) -> list[TaskOut]:
        active = (
            db.execute(select(Shift).where(Shift.ended_at.is_(None)).order_by(Shift.id.desc()))
            .scalars()
            .first()
        )
        if not active:
            return []
        tasks = (
            db.execute(select(Task).where(Task.shift_id == active.id).order_by(Task.id.desc()))
            .scalars()
            .all()
        )
        return [_task_out(t) for t in tasks]

    @app.post("/api/tasks", response_model=TaskOut)
    def task_add(payload: TaskIn, db: Session = Depends(get_db)) -> TaskOut:
        active = (
            db.execute(select(Shift).where(Shift.ended_at.is_(None)).order_by(Shift.id.desc()))
            .scalars()
            .first()
        )
        t = Task(title=payload.title.strip(), shift_id=active.id if active else None, completed_at=None)
        db.add(t)
        db.commit()
        db.refresh(t)
        return _task_out(t)

    @app.post("/api/tasks/{task_id}/complete", response_model=TaskOut)
    def task_complete(task_id: int, db: Session = Depends(get_db)) -> TaskOut:
        t = db.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found.")
        t.completed_at = _utcnow()
        db.add(t)
        db.commit()
        db.refresh(t)
        return _task_out(t)

    @app.post("/api/tasks/{task_id}/reopen", response_model=TaskOut)
    def task_reopen(task_id: int, db: Session = Depends(get_db)) -> TaskOut:
        t = db.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found.")
        t.completed_at = None
        db.add(t)
        db.commit()
        db.refresh(t)
        return _task_out(t)

    @app.delete("/api/tasks/{task_id}")
    def task_delete(task_id: int, db: Session = Depends(get_db)) -> dict:
        t = db.get(Task, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found.")
        db.delete(t)
        db.commit()
        return {"ok": True}

    @app.get("/api/system", response_model=SystemOut)
    def system() -> dict:
        return read_system_snapshot()

    return app

