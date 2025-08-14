#!/usr/bin/env python3
"""
Strategy Translation API Endpoint
Provides AI-powered translation from Pine Script/MQL4/MQL5 to Python
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add the strategies directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies'))
from strategy_translator import translate_to_python, detect_language

router = APIRouter(prefix="/translate", tags=["translation"])

class TranslationRequest(BaseModel):
    code: str
    source_language: Optional[str] = None
    target_language: str = "python"

class TranslationResponse(BaseModel):
    success: bool
    translated_code: Optional[str] = None
    source_language: str
    target_language: str
    translation_method: str
    error: Optional[str] = None
    metadata: Optional[dict] = None

@router.post("/strategy", response_model=TranslationResponse)
async def translate_strategy(request: TranslationRequest):
    """
    Translate a trading strategy from Pine Script/MQL4/MQL5 to Python
    """
    try:
        # Detect language if not provided
        source_lang = request.source_language or detect_language(request.code)
        
        # Translate to Python
        translated_code, metadata = translate_to_python(request.code, source_lang)
        
        return TranslationResponse(
            success=True,
            translated_code=translated_code,
            source_language=source_lang,
            target_language=request.target_language,
            translation_method=metadata.get("via", "ai"),
            metadata=metadata
        )
        
    except ValueError as e:
        # AI translation failed
        return TranslationResponse(
            success=False,
            source_language=request.source_language or "unknown",
            target_language=request.target_language,
            translation_method="ai",
            error=str(e)
        )
        
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )

@router.post("/detect-language")
async def detect_strategy_language(request: TranslationRequest):
    """
    Detect the programming language of the provided strategy code
    """
    try:
        detected_lang = detect_language(request.code)
        return {
            "success": True,
            "detected_language": detected_lang,
            "code_preview": request.code[:200] + "..." if len(request.code) > 200 else request.code
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Language detection failed: {str(e)}"
        ) 