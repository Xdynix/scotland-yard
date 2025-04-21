from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def hello_world() -> dict[str, str]:
    return {"message": "Hello World!"}
