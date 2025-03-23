import json
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

# Import additional needed modules
from sqlmodel import Session, func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.db import engine  # You'll need access to your engine
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


def run_crawler_task(
    history_id: uuid.UUID,
    city: str,
    price_min: float,
    price_max: float,
    stars: float,
):
    """
    Background task to run both booking and agoda spiders and save/match results
    """

    session = Session(engine)
    try:
        # Calculate checkin/checkout dates
        tomorrow = datetime.now() + timedelta(days=1)
        day_after_tomorrow = tomorrow + timedelta(days=1)
        checkin = tomorrow.strftime("%Y-%m-%d")
        checkout = day_after_tomorrow.strftime("%Y-%m-%d")

        # Format price range and hotel class for booking.com
        price_range = f"BDT-{int(price_min)}-{int(price_max)}-1"
        hotel_class = str(int(stars))

        # Step 1: Run the booking_spider
        booking_results_file = f"booking_results_{history_id}.json"
        booking_cmd = [
            "scrapy",
            "crawl",
            "booking_spider",
            "-a",
            f"location={city}",
            "-a",
            f"checkin={checkin}",
            "-a",
            f"checkout={checkout}",
            "-a",
            f"price_range={price_range}",
            "-a",
            f"hotel_class={hotel_class}",
            "-o",
            booking_results_file,
        ]

        print(f"Running booking.com crawler: {' '.join(booking_cmd)}")

        booking_process = subprocess.Popen(
            booking_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        booking_stdout, booking_stderr = booking_process.communicate()
        booking_results = []

        # Process booking.com results
        try:
            # Update history status to in-progress
            scrapped_history = session.get(ScrappedItemsHistory, history_id)
            scrapped_history.scrape_status = "booking_spider_completed"
            session.commit()
            session.refresh(scrapped_history)

            with open(booking_results_file) as f:
                booking_results = json.load(f)

            print(f"Scraped {len(booking_results)} items from booking.com")

            # Create all items in a list
            scraped_items = [
                ScrappedItem(
                    title=result.get("title", "Unknown"),
                    price_booking=float(result.get("price", 0))
                    if result.get("price")
                    else 0,
                    url_booking=result.get("url", ""),
                    stars=float(result.get("stars", 0))
                    if result.get("stars")
                    else None,
                    image_url=result.get("image_url", None),
                    history_id=history_id,
                )
                for result in booking_results
            ]

            # Bulk add all items
            session.bulk_save_objects(scraped_items)
            session.commit()

        except Exception as e:
            print(f"Error processing booking.com results: {str(e)}")
            scrapped_history = session.get(ScrappedItemsHistory, history_id)
            scrapped_history.scrape_status = f"booking_failed: {str(e)}"
            session.commit()
            session.refresh(scrapped_history)
            return

        # Step 2: Run the agoda_spider
        agoda_results_file = f"agoda_results_{history_id}.json"

        # Update history status
        scrapped_history = session.get(ScrappedItemsHistory, history_id)
        scrapped_history.scrape_status = "running_agoda_spider"
        session.commit()

        # Format parameters for Agoda
        agoda_cmd = [
            "scrapy",
            "crawl",
            "agoda_spider",
            "-a",
            f"location={city}",
            "-a",
            f"checkin={checkin}",
            "-a",
            f"checkout={checkout}",
            "-a",
            f"adults={2}",  # Default to 2 adults
            "-a",
            f"rooms={1}",  # Default to 1 room
            "-a",
            f"hotel_star_rating={int(stars)}",
            "-a",
            f"price_from={int(price_min)}",
            "-a",
            f"price_to={int(price_max)}",
            "-o",
            agoda_results_file,
        ]

        print(f"Running Agoda crawler: {' '.join(agoda_cmd)}")

        agoda_process = subprocess.Popen(
            agoda_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        agoda_stdout, agoda_stderr = agoda_process.communicate()
        print(f"Agoda stdout: {agoda_stdout}")
        print(f"Agoda stderr: {agoda_stderr}")

        try:
            with open(agoda_results_file) as f:
                agoda_results = json.load(f)

            print(f"Scraped {len(agoda_results)} items from Agoda")

            # Step 3: Match results from both sources by title similarity
            # Get all scraped items for this history
            statement = select(ScrappedItem).where(
                ScrappedItem.history_id == history_id
            )
            scraped_items = session.exec(statement).all()

            # Create a mapping for fuzzy matching hotel names
            from difflib import SequenceMatcher

            def similar(a, b):
                return SequenceMatcher(None, a.lower(), b.lower()).ratio()

            # For each Agoda result, find the best match in our database
            match_count = 0
            for agoda_item in agoda_results:
                agoda_title = agoda_item.get("title", "")
                if not agoda_title:
                    continue

                best_match = None
                best_score = 0.8  # Threshold for a good match

                for db_item in scraped_items:
                    score = similar(agoda_title, db_item.title)
                    if score > best_score:
                        best_score = score
                        best_match = db_item

                # If we found a good match, update with Agoda data
                if best_match:
                    match_count += 1
                    best_match.price_agoda = (
                        float(agoda_item.get("price", "0").replace("$", "").strip())
                        * 122
                    )
                    best_match.url_agoda = agoda_item.get("url", "")
                    best_match.updated_at = datetime.now()

            session.commit()
            print(f"Matched and updated {match_count} items with Agoda data")

            # Update history status to completed
            scrapped_history = session.get(ScrappedItemsHistory, history_id)
            scrapped_history.scrape_status = "completed"
            session.commit()
            session.refresh(scrapped_history)

        except Exception as e:
            print(f"Error processing Agoda results: {str(e)}")
            scrapped_history = session.get(ScrappedItemsHistory, history_id)
            scrapped_history.scrape_status = f"agoda_failed: {str(e)}"
            session.commit()
            session.refresh(scrapped_history)

    except Exception as e:
        print(f"Background task error: {str(e)}")
        try:
            scrapped_history = session.get(ScrappedItemsHistory, history_id)
            scrapped_history.scrape_status = f"failed: {str(e)}"
            session.commit()
        except Exception as e:
            scrapped_history = session.get(ScrappedItemsHistory, history_id)
            print(f"Could not update history status: {str(e)}")
            scrapped_history.scrape_status = f"failed: {str(e)}"
            session.commit()
            session.refresh(scrapped_history)
    finally:
        # Clean up temporary files
        for file in [
            f"booking_results_{history_id}.json",
            f"agoda_results_{history_id}.json",
        ]:
            if os.path.exists(file):
                os.remove(file)
        print("Background task completed")


@router.get("/history", response_model=ScrappedItemsHistoriesPublic)
async def read_scrapped_history(
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
async def create_scrapped_history(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    history_in: ScrappedItemsHistoryCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Create new scrapped items history and start crawler.
    """
    # Set default values if not provided
    city = history_in.city or "Dhaka"
    price_min = history_in.price_min or 1500
    price_max = history_in.price_max or 25500
    stars = history_in.stars or 3

    history_in_private = history_in.model_dump()
    history_in_private["scrape_status"] = "pending"
    history = ScrappedItemsHistory.model_validate(
        history_in_private, update={"owner_id": current_user.id}
    )

    session.add(history)
    session.commit()
    session.refresh(history)

    # Add background task to run crawler
    background_tasks.add_task(
        run_crawler_task,
        history_id=history.id,
        city=city,
        price_min=price_min,
        price_max=price_max,
        stars=stars,
    )

    return history


@router.get("/history/{id}", response_model=ScrappedItemsHistory)
async def read_scrapped_history_by_id(
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
async def read_scrapped_items(
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
        .join(ScrappedItemsHistory)
        .where(ScrappedItemsHistory.owner_id == current_user.id)
        .order_by(ScrappedItem.created_at.desc())
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
async def create_scrapped_item(
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
async def bookmark_scrapped_item(
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
async def read_bookmarked_items(
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
async def delete_bookmark(
    session: SessionDep, current_user: CurrentUser, item_id: uuid.UUID
) -> Message:
    """
    Delete a bookmarked item.
    """
    statement = select(BookMarkedScrappedItem).where(
        BookMarkedScrappedItem.scrapped_item_id == item_id,
        BookMarkedScrappedItem.owner_id == current_user.id,
    )
    bookmark = session.exec(statement).one_or_none()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    if not current_user.is_superuser and (bookmark.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(bookmark)
    session.commit()
    return Message(message="Bookmark deleted successfully")
