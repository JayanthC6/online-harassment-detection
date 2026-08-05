from ml.predict import predict_message as predict_baseline
import ml.predict_transformer as predict_transformer
from services.admin_service import AdminService

try:
    import ml.explain as explain_module
    _explain_available = True
except Exception:
    _explain_available = False

_similarity_available = False
try:
    from ml.similarity import find_similar_reports
    _similarity_available = True
except Exception:
    pass

CATEGORY_TO_CLASS = {"hate_speech": 0, "offensive_language": 1, "none": 2}
CATEGORY_RISK_BASE = {
    "hate_speech": 80,
    "offensive_language": 50,
    "none": 5,
}

class PredictionService:
    @staticmethod
    def get_active_model_name() -> str:
        return "distilbert" if predict_transformer.is_available() else "baseline"

    @staticmethod
    def compute_risk_score(category: str, confidence: float) -> float:
        base = CATEGORY_RISK_BASE.get(category, 5)
        score = base * confidence
        return round(min(100, max(0, score)), 1)

    @staticmethod
    def classify_text(text: str) -> dict:
        if predict_transformer.is_available():
            return predict_transformer.predict_message(text)
        
        result = predict_baseline(text)
        result["model"] = "baseline"

        if _explain_available and result.get("category"):
            class_idx = CATEGORY_TO_CLASS.get(result["category"])
            if class_idx is not None:
                result["explanation"] = explain_module.explain_prediction(
                    text, class_idx, top_n=5
                )
        return result

    @staticmethod
    def attach_risk_and_similarity(result: dict, text_for_embedding: str) -> dict:
        result["risk_score"] = PredictionService.compute_risk_score(
            result.get("category", "none"),
            result.get("confidence", 0),
        )

        if result["label"] == "harassing" and _similarity_available:
            try:
                existing = AdminService.get_all_flagged()
                matches, embedding = find_similar_reports(text_for_embedding, existing)
                result["embedding"] = embedding
                if matches:
                    result["similar_reports"] = matches[:3]
                    result["cluster_id"] = f"cluster-{hash(matches[0]['text_preview']) % 10000:04d}"
            except Exception:
                pass 

        return result
