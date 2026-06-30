from fastapi import FastAPI


def create_app() -> FastAPI:
    return FastAPI(title="Fynd")


app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
