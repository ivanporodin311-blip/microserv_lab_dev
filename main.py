import os
import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# --- Настройка логирования (Опциональное требование) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Настройка БД ---
# Берем URL из переменных окружения (как в docker-compose) или используем дефолтный для локальной разработки
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/microservice_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Модель данных (Таблица в PostgreSQL) ---
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    year = Column(Integer)

# Создаем таблицы при запуске (для простоты лабораторной)
Base.metadata.create_all(bind=engine)

# --- Pydantic схемы для валидации входных данных ---
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Название книги обязательно")
    author: str = Field(..., min_length=1, description="Автор обязателен")
    year: int = Field(..., gt=1000, lt=3000, description="Год должен быть корректным")

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    year: int

    class Config:
        from_attributes = True

# --- Инициализация приложения ---
app = FastAPI(title="Microservice Lab: Book Catalog")

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 1. GET: Получить все книги ---
@app.get("/books", response_model=list[BookResponse])
def get_all_books(db: Session = Depends(get_db)):
    logger.info("Запрос на получение всех книг")
    return db.query(Book).all()

# --- 2. GET: Получить книгу по ID ---
@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        logger.warning(f"Попытка получить несуществующую книгу с ID: {book_id}")
        # Требование 8: не падаем, а возвращаем HTTP-код ошибки
        raise HTTPException(status_code=404, detail="Книга с таким ID не найдена")
    return book

# --- 3. POST: Добавить новую книгу ---
@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    logger.info(f"Попытка создать книгу: {book.title}")
    db_book = Book(title=book.title, author=book.author, year=book.year)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    logger.info(f"Книга успешно создана с ID: {db_book.id}")
    return db_book

# --- 4. DELETE: Удалить книгу по ID ---
@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        logger.warning(f"Попытка удалить несуществующую книгу с ID: {book_id}")
        raise HTTPException(status_code=404, detail="Книга для удаления не найдена")
    
    db.delete(book)
    db.commit()
    logger.info(f"Книга с ID {book_id} успешно удалена")
    return {"message": "Книга успешно удалена"}