from fastapi import FastAPI


def create_app() -> FastAPI:
    application = FastAPI(
        title="A 股自选股风险监控 Agent",
        version="0.1.0",
    )

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
