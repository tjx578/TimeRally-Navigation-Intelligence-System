from fastapi import FastAPI

from app.routers import exports, places, probability, rally, routing, validation


app = FastAPI(
    title="Time Rally Navigation Intelligence System",
    version="0.1.0",
)

app.include_router(rally.router, prefix="/v1/rally", tags=["rally"])
app.include_router(places.router, prefix="/v1/places", tags=["places"])
app.include_router(routing.router, prefix="/v1/routing", tags=["routing"])
app.include_router(validation.router, prefix="/v1/validation", tags=["validation"])
app.include_router(exports.router, prefix="/v1/export", tags=["export"])
app.include_router(probability.router, prefix="/v1/probability", tags=["probability"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
