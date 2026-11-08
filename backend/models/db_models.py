from sqlmodel import SQLModel, Field
import uuid
from typing import Optional


class Files(SQLModel, table=True):
    full_file_name: str = Field(primary_key=True)


class Subject(SQLModel, table=True):
    subject_id: str = Field(primary_key=True)
    subject: str = Field(unique=True)


class Category(SQLModel, table=True):
    category_id: str = Field(primary_key=True)
    category_name: str = Field(unique=True)


class Term(SQLModel, table=True):
    term_id: str = Field(
        primary_key=True,
        index=True
    )
    file_of_origin: str = Field(foreign_key="files.full_file_name")
    category_id: str = Field(foreign_key="category.category_id")
    subject_id: str = Field(foreign_key="subject.subject_id")
    term: str = Field(unique=True)
    definition: str
