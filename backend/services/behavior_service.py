from datetime import datetime, timezone
import uuid
from core.database import db_instance
from core.logger import logger
from ml.behavior import calculate_behavior_score

class BehaviorService:
    @staticmethod
    def _get_profile(actor_id):
        if not actor_id:
            return None
        return db_instance.get_profile(actor_id)

    @staticmethod
    def _save_profile(profile):
        db_instance.save_profile(profile)

    @staticmethod
    def _create_initial_profile(actor_id):
        return {
            "actor_id": actor_id,
            "first_seen": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "total_reports": 0,
            "safe_messages": 0,
            "harmful_messages": 0,
            "highest_risk": 0,
            "avg_risk": 0.0,
            "multi_label_distribution": {},
            "behavior_score": 0.0,
            "behavior_level": "Safe",
            "recommendation": "Safe / No action required",
            "explanation": [],
            "timeline": []
        }

    @staticmethod
    def log_incident(actor_id, message_prediction):
        """
        Updates the profile incrementally with a new message prediction.
        """
        if not actor_id or str(actor_id).strip() == "" or actor_id.lower() == "anonymous":
            actor_id = f"anon_{uuid.uuid4().hex[:8]}"

        profile = BehaviorService._get_profile(actor_id)
        if not profile:
            profile = BehaviorService._create_initial_profile(actor_id)
            
        # Extract stats from prediction
        risk_score = message_prediction.get("risk_score")
        effective_score = float(risk_score) if risk_score is not None else 0.0
        is_harmful = message_prediction.get("label") == "harassing"
        primary_cat = message_prediction.get("category", "clean")
        
        # Update raw stats
        profile["last_seen"] = datetime.now(timezone.utc).isoformat()
        profile["total_reports"] += 1
        
        if is_harmful:
            profile["harmful_messages"] += 1
        else:
            profile["safe_messages"] += 1
            
        profile["highest_risk"] = max(profile["highest_risk"], effective_score)
        
        # Incremental average risk
        total_risk = (profile["avg_risk"] * (profile["total_reports"] - 1)) + effective_score
        profile["avg_risk"] = total_risk / profile["total_reports"]
        
        # Update category distribution
        cat_key = primary_cat.replace('_', ' ').title()
        if cat_key not in profile["multi_label_distribution"]:
            profile["multi_label_distribution"][cat_key] = 0
        profile["multi_label_distribution"][cat_key] += 1
        
        # Optional: capture secondary categories if they exist
        secondary = message_prediction.get("secondary_labels", {})
        for sec, _ in secondary.items():
            if sec not in profile["multi_label_distribution"]:
                profile["multi_label_distribution"][sec] = 0
            profile["multi_label_distribution"][sec] += 1

        # Calculate new score
        old_level = profile.get("behavior_level")
        score, level, rec, explanation = calculate_behavior_score(profile)
        
        profile["behavior_score"] = score
        profile["behavior_level"] = level
        profile["recommendation"] = rec
        profile["explanation"] = explanation
        
        # Update timeline if level changed or it's the first time
        if old_level != level or not profile["timeline"]:
            profile["timeline"].append({
                "timestamp": profile["last_seen"],
                "level": level,
                "reason": explanation[-1] if explanation else "Level changed"
            })
            
        BehaviorService._save_profile(profile)
        return actor_id

    @staticmethod
    def log_conversation_incidents(messages):
        """
        Process an array of conversation messages and update their senders' profiles.
        """
        for msg in messages:
            actor = msg.get("sender")
            pred = msg.get("prediction")
            if actor and pred:
                BehaviorService.log_incident(actor, pred)

    @staticmethod
    def get_all_profiles():
        return db_instance.get_all_profiles()
