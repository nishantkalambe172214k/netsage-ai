from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.cases import router as cases_router
from app.api.diagnoses import router as diagnoses_router
from app.api.rule_findings import router as rule_findings_router
from app.api.reviews import router as reviews_router
from app.api.verification import router as verification_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="", tags=["Health"])
api_router.include_router(cases_router, prefix="/cases", tags=["Cases"])
api_router.include_router(diagnoses_router, prefix="/diagnoses", tags=["Diagnoses"])
api_router.include_router(rule_findings_router, prefix="/rule-findings", tags=["Rule Findings"])
api_router.include_router(reviews_router, prefix="/reviews", tags=["Human Reviews"])
api_router.include_router(verification_router, prefix="/verification", tags=["Verification"])
