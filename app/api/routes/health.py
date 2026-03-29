from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def read_root():
    return {"service": "Projeto Apolo", "status": "ok"}


@router.get("/health")
def health_check():
    return {"service": "Projeto Apolo", "status": "running"}