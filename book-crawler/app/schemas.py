from pydantic import BaseModel

class BookCreate(BaseModel): #응답 모델 정의
    book_name: str
    book_image: str
    author: str
    publisher: str
    summary: str
    isbn: str