import os
import threading
from typing import Dict, Any, Tuple
from .base import ModelAdapter
from .threat_intel import mask_pii

# We lazy load NLLB and lingua to avoid unnecessary memory consumption
_translator = None
_language_detector = None
_model_lock = threading.Lock()

def _get_language_detector():
    # langdetect is pure python and loads eagerly on import, no builder needed
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    return detect

_tokenizer = None

def _get_translator():
    global _translator, _tokenizer
    if _translator is None:
        with _model_lock:
            if _translator is None:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
                from huggingface_hub import snapshot_download
                model_id = "facebook/nllb-200-distilled-600M"
                model_path = snapshot_download(repo_id=model_id, local_files_only=False)
                _tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
                _translator = AutoModelForSeq2SeqLM.from_pretrained(model_path, local_files_only=True)
    return _translator, _tokenizer

# NLLB uses BCP-47 codes.
NLLB_LANG_CODES = {
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "ta": "tam_Taml",
    "te": "tel_Telu"
}

# Map langdetect ISO codes to full names for UI
LANG_NAMES = {
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "en": "English"
}

class MultilingualAdapter(ModelAdapter):
    def __init__(self, base_adapter: ModelAdapter):
        self.base_adapter = base_adapter
        
    def _detect_and_translate(self, text: str) -> Tuple[str, Dict[str, Any]]:
        meta = {
            "enabled": True,
            "detected_language": "Unknown",
            "language_code": "unknown",
            "translation_status": "not_required",
            "analysis_mode": "original_text_fallback"
        }
        
        # PII mask the original text before doing anything
        masked_text = mask_pii(text)
        
        try:
            detect_func = _get_language_detector()
            # langdetect throws LangDetectException if text is too short or has no letters
            lang_code = detect_func(masked_text)
            
            meta["language_code"] = lang_code
            meta["detected_language"] = LANG_NAMES.get(lang_code, "Unknown")
            
            if lang_code == "en":
                meta["enabled"] = False
                meta["analysis_mode"] = "original"
                return text, meta
                
            if lang_code not in NLLB_LANG_CODES:
                meta["enabled"] = False
                meta["analysis_mode"] = "original"
                return text, meta
            
            try:
                model, tokenizer = _get_translator()
                src_lang = NLLB_LANG_CODES[lang_code]
                
                tokenizer.src_lang = src_lang
                inputs = tokenizer(masked_text, return_tensors="pt")
                tgt_lang_id = tokenizer.convert_tokens_to_ids("eng_Latn")
                
                outputs = model.generate(
                    **inputs,
                    forced_bos_token_id=tgt_lang_id,
                    max_length=512
                )
                translated_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
                
                meta["translation_status"] = "success"
                meta["analysis_mode"] = "translated"
                meta["translated_text"] = translated_text
                
                return translated_text, meta
                
            except Exception as e:
                print(f"Translation failed: {e}")
                meta["translation_status"] = "failed"
                meta["analysis_mode"] = "original_text_fallback"; meta["debug_error"] = str(e)
                return text, meta
                
        except Exception as e:
            import traceback
            print(f"Language detection failed explicitly: {type(e).__name__}: {e}")
            traceback.print_exc()
            meta["translation_status"] = "failed"
            meta["analysis_mode"] = "original_text_fallback"; meta["debug_error"] = str(e)
            return text, meta

    def predict(self, text: str) -> Dict[str, Any]:
        analysis_text, translation_meta = self._detect_and_translate(text)
        
        # Call the next adapter in the chain with the potentially translated (and masked) text
        result = self.base_adapter.predict(analysis_text)
        
        # Inject metadata safely
        result["multilingual_analysis"] = translation_meta
        
        if translation_meta.get("analysis_mode") == "translated":
            result["_translated_text"] = analysis_text
            
        return result
