from fastapi import FastAPI
from videoanalysis.api import router
from common.kafka.producer import shutdown_producer

app = FastAPI(title="Video Analysis API")
app.include_router(router)

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_producer()