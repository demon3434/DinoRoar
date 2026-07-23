import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Person, User
from ..schemas import PersonSyncPayload, PersonResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/persons", tags=["Persons"])
logger = logging.getLogger("DinoRoar.persons")

@router.post("/sync", response_model=List[PersonResponse])
async def sync_persons(
    payload: PersonSyncPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Offline-first synchronization endpoint for Persons.
    Merges local client modifications and hard-deletes removed persons.
    Returns the complete list of active persons for the user.
    """
    # 1. Process client deletions (Logical Soft Delete)
    if payload.deleted_uuids:
        to_delete = db.query(Person).filter(
            Person.uuid.in_(payload.deleted_uuids),
            Person.user_id == current_user.id
        ).all()
        
        for person in to_delete:
            person.is_deleted = True
        db.commit()
        logger.info(f"Sync: Soft deleted {len(to_delete)} persons for user {current_user.username}")

    # 2. Process client additions/updates
    for person_data in payload.persons:
        existing_person = db.query(Person).filter(
            Person.uuid == person_data.uuid,
            Person.user_id == current_user.id
        ).first()

        if existing_person:
            # Update fields
            existing_person.name = person_data.name
            existing_person.abbreviation = person_data.abbreviation
            existing_person.relationship = person_data.relationship
            existing_person.category_uuid = person_data.category_uuid
            existing_person.sort_order = person_data.sort_order
            existing_person.color_tag = person_data.color_tag
            existing_person.is_temporary = person_data.is_temporary
            existing_person.is_deleted = person_data.is_deleted
        else:
            # Create new person record
            new_person = Person(
                user_id=current_user.id,
                uuid=person_data.uuid,
                name=person_data.name,
                abbreviation=person_data.abbreviation,
                relationship=person_data.relationship,
                category_uuid=person_data.category_uuid,
                sort_order=person_data.sort_order,
                color_tag=person_data.color_tag,
                is_temporary=person_data.is_temporary,
                is_deleted=person_data.is_deleted
            )
            db.add(new_person)
            
    db.commit()

    # 3. Fetch all persons of the user (including logical deleted ones to resolve history labels)
    active_persons = db.query(Person).filter(
        Person.user_id == current_user.id
    ).all()

    return active_persons
