from pydantic import BaseModel


class User(BaseModel):
    id: str | None = None
    email: str = ""
    name: str = ""
    age: int | None = None
    assistant_name: str = "Jarvis"
