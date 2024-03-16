from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging

class TODO(SQLModel, table=True):
    id: int = Field(primary_key=True)
    text: str = Field(index=True)
    is_done: bool = Field(default=False)
    
db_url = ""
# sqlite_file_name = "database.db"
# sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(db_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def main():
    create_db_and_tables()

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    

@app.post("/create/")
def create_todo(text: str):
    try:
        with Session(engine) as session:
            todo = TODO(text=text)
            session.add(todo)
            session.commit()
            session.refresh(todo)
            todo_dict = jsonable_encoder(todo) 
            return JSONResponse(status_code=201, content={"message": "Todo created successfully", "todo": todo_dict})
    except Exception as e:
        logging.error(f"An error occurred while creating todo: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})

@app.get("/")
def read_todos():
    with Session(engine) as session:
        todos = session.exec(select(TODO)).all()
        return todos

@app.get("/done")
def get_completed():
    with Session(engine) as session:
        todos_query = session.query(TODO)
        done_todo_query = todos_query.filter(TODO.is_done == True)
        return done_todo_query.all()

@app.put("/update/{id}")
async def update_todo(
    id: int,
    new_text: str = "",
    is_complete: bool = False
):
    with Session(engine) as session:
        todo_query = session.query(TODO).filter(TODO.id==id)
        todo = todo_query.first()
        if new_text:
            todo.text = new_text
        todo.is_done = is_complete
        session.add(todo)
        session.commit()
        return {"status" : "success"}

@app.delete("/delete/{id}")
async def delete_todo(id: int):
    with Session(engine) as session:
        todo = session.query(TODO).filter(TODO.id==id).first() # Todo object
        session.delete(todo)
        session.commit()
        return {"todo deleted": todo.text}


if __name__ == "__main__":
    main()