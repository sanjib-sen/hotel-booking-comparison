import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    scrapped_items_history: list["ScrappedItemsHistory"] = Relationship(
        back_populates="owner", cascade_delete=True
    )
    bookmarked_scrapped_items: list["BookMarkedScrappedItem"] = Relationship(
        back_populates="owner", cascade_delete=True
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class ScrappedItemsHistoryBase(SQLModel):
    city: str = Field(min_length=1, default="Dhaka", max_length=255)
    price_min: float | None = Field(default=0, ge=0)
    price_max: float | None = Field(default=25000, ge=0)
    stars: float | None = Field(default=3, ge=0, le=5)


class ScrappedItemsHistoryPublic(ScrappedItemsHistoryBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    price_min: float | None
    price_max: float | None
    stars: float | None
    scrapped_time: datetime
    scrape_status: str


class ScrappedItemsHistoriesPublic(ScrappedItemsHistoryBase):
    data: list[ScrappedItemsHistoryPublic]
    count: int


class ScrappedItemsHistoryCreate(ScrappedItemsHistoryBase):
    city: str | None = Field(default=None, min_length=1, max_length=255)
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    stars: float | None = Field(default=None, ge=0, le=5)


class ScrappedItemsHistory(ScrappedItemsHistoryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    scrape_status: str = Field(min_length=1, max_length=255)
    owner: User = Relationship(back_populates="scrapped_items_history")
    scrapped_time: datetime = Field(default_factory=datetime.now)
    scrapped_items: list["ScrappedItem"] = Relationship(
        back_populates="history", cascade_delete=True
    )


class ScrappedItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    price_booking: float = Field(ge=0)
    url_booking: str = Field(min_length=1)
    stars: float | None = Field(default=None, ge=0, le=5)
    image_url: str | None = Field(default=None, max_length=255)


class ScrappedItem(ScrappedItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    price_agoda: float | None = Field(default=None, ge=0)
    url_agoda: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    history_id: uuid.UUID = Field(
        foreign_key="scrappeditemshistory.id", nullable=False, ondelete="CASCADE"
    )
    history: ScrappedItemsHistory | None = Relationship(back_populates="scrapped_items")


class ScrappedItemPublic(ScrappedItemBase):
    id: uuid.UUID
    title: str
    price_booking: float
    url_booking: str
    stars: float | None
    image_url: str | None


class ScrappedItemsPublic(SQLModel):
    data: list[ScrappedItemPublic]
    count: int


class BookMarkedScrappedItem(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="bookmarked_scrapped_items")
    bookmarked_at: datetime = Field(default_factory=datetime.now)
    scrapped_item_id: uuid.UUID = Field(
        foreign_key="scrappeditem.id", nullable=False, ondelete="CASCADE"
    )


class BookMarkedScrappedItemCreate(SQLModel):
    pass


class ScrappedItemCreate(ScrappedItemBase):
    pass
