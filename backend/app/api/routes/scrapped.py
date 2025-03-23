import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    BookMarkedScrappedItem,
    Message,
    ScrappedItem,
    ScrappedItemCreate,
    ScrappedItemsHistoriesPublic,
    ScrappedItemsHistory,
    ScrappedItemsHistoryCreate,
    ScrappedItemsPublic,
)

router = APIRouter(prefix="/scrapped", tags=["scrapped"])


@router.get("/history", response_model=ScrappedItemsHistoriesPublic)
def read_scrapped_history(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve scrapped items history.
    """
    if current_user.is_superuser:
        statement = select(ScrappedItemsHistory).offset(skip).limit(limit)
        count_statement = select(func.count()).select_from(ScrappedItemsHistory)
        count = session.exec(count_statement).one()
    else:
        statement = (
            select(ScrappedItemsHistory)
            .where(ScrappedItemsHistory.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        count_statement = (
            select(func.count())
            .select_from(ScrappedItemsHistory)
            .where(ScrappedItemsHistory.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
    return ScrappedItemsHistoriesPublic(
        data=session.exec(statement).all(),
        count=count,
    )


@router.post("/history", response_model=ScrappedItemsHistory)
def create_scrapped_history(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    history_in: ScrappedItemsHistoryCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Create new scrapped items history and start crawler.
    """
    history_in_private = history_in.model_dump()
    history_in_private["scrape_status"] = "pending"
    history = ScrappedItemsHistory.model_validate(
        history_in_private, update={"owner_id": current_user.id}
    )

    tomorrow = datetime.now() + timedelta(days=1)
    day_after_tomorrow = tomorrow + timedelta(days=1)

    # Format price range for Booking.com
    price_range = f"BDT-{history_in.price_min}-{history_in.price_max}-1"

    session.add(history)
    session.commit()
    session.refresh(history)

    # Add background task to run crawler
    # background_tasks.add_task(
    #     run_booking_crawler_task,
    #     history_id=history.id,
    #     location=f"{history_in.city}, Bangladesh",
    #     checkin=tomorrow.strftime("%Y-%m-%d"),
    #     checkout=day_after_tomorrow.strftime("%Y-%m-%d"),
    #     price_range=price_range,
    #     hotel_class=history_in.stars,
    #     session=session,
    # )

    return history


@router.get("/history/{id}", response_model=ScrappedItemsHistory)
def read_scrapped_history_by_id(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get scrapped history by ID.
    """
    history = session.get(ScrappedItemsHistory, id)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    if not current_user.is_superuser and (history.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return history


@router.get("/items/{history_id}", response_model=ScrappedItemsPublic)
def read_scrapped_items(
    session: SessionDep,
    current_user: CurrentUser,
    history_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve scrapped items for a specific history.
    """

    statement = (
        select(ScrappedItem)
        .where(ScrappedItem.history_id == history_id)
        .offset(skip)
        .limit(limit)
    )
    count_statement = (
        select(func.count())
        .select_from(ScrappedItem)
        .where(ScrappedItem.history_id == history_id)
    )
    count = session.exec(count_statement).one()
    return ScrappedItemsPublic(
        data=session.exec(statement).all(),
        count=count,
    )


@router.post("/items/{history_id}", response_model=ScrappedItem)
def create_scrapped_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    history_id: uuid.UUID,
    item_in: ScrappedItemCreate,
) -> Any:
    """
    Create new scrapped item.
    """
    history = session.get(ScrappedItemsHistory, history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    if not current_user.is_superuser and (history.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    item = ScrappedItem.model_validate(item_in, update={"history_id": history_id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.post("/bookmark/{item_id}", response_model=BookMarkedScrappedItem)
def bookmark_scrapped_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> Any:
    """
    Bookmark a scrapped item.
    """
    item = session.get(ScrappedItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.history.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    bookmark = BookMarkedScrappedItem(
        scrapped_item_id=item_id,
        owner_id=current_user.id,
    )
    session.add(bookmark)
    session.commit()
    session.refresh(bookmark)
    return bookmark


@router.get("/bookmarks", response_model=list[BookMarkedScrappedItem])
def read_bookmarked_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve bookmarked scrapped items.
    """
    if current_user.is_superuser:
        statement = select(BookMarkedScrappedItem).offset(skip).limit(limit)
    else:
        statement = (
            select(BookMarkedScrappedItem)
            .where(BookMarkedScrappedItem.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
    return session.exec(statement).all()


@router.delete("/bookmark/{item_id}")
def delete_bookmark(
    session: SessionDep, current_user: CurrentUser, item_id: uuid.UUID
) -> Message:
    """
    Delete a bookmarked item.
    """
    bookmark = session.get(BookMarkedScrappedItem, item_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    if not current_user.is_superuser and (bookmark.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(bookmark)
    session.commit()
    return Message(message="Bookmark deleted successfully")
