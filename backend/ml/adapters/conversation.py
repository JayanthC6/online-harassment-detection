from typing import List, Dict
from .base import ModelAdapter
from .heuristic import HeuristicMultiLabelAdapter
import uuid
from datetime import datetime, timezone

class ConversationAdapter:
    def __init__(self, message_adapter: ModelAdapter):
        """
        Wraps a single-message ModelAdapter to evaluate an entire conversation.
        """
        self.message_adapter = message_adapter

    def predict_conversation(self, messages: List[Dict]) -> Dict:
        """
        messages is a list of dicts, e.g. [{"text": "Hello", "sender": "User1", "timestamp": "..."}]
        Returns a structured conversation result.
        """
        if not messages:
            raise ValueError("Conversation must contain at least one message.")

        # 1. Analyze each message individually
        analyzed_messages = []
        for i, msg in enumerate(messages):
            text = msg.get("text", "")
            sender = msg.get("sender", f"User {i%2 + 1}")
            timestamp = msg.get("timestamp", datetime.now(timezone.utc).isoformat())

            # Predict using underlying adapter
            prediction = self.message_adapter.predict(text)
            
            analyzed_messages.append({
                "message_id": str(uuid.uuid4()),
                "text": text,
                "sender": sender,
                "timestamp": timestamp,
                "prediction": prediction
            })

        # 2. Contextual Escalation Intelligence & Aggregate Stats
        escalation_score = 0
        escalation_level = "None"
        escalation_reason = []
        conversation_risk = 0
        
        # Stats
        total_messages = len(analyzed_messages)
        per_category_counts = {}
        high_risk_message_count = 0
        threat_labeled_count = 0
        
        # Pass 1: compute risk for all messages and gather stats
        for msg in analyzed_messages:
            pred = msg["prediction"]
            primary_cat = pred.get("primary_label", pred.get("category", "none"))
            conf = pred.get("confidence", 0)
            
            from services.prediction_service import PredictionService
            msg_risk = PredictionService.compute_risk_score(
                primary_cat, conf, pred.get("secondary_labels", {})
            )
            msg["risk_score"] = msg_risk
            
            conversation_risk = max(conversation_risk, msg_risk)
            
            if msg_risk >= 70:
                high_risk_message_count += 1
            if primary_cat == "Threat":
                threat_labeled_count += 1
                
            if primary_cat != "Clean":
                per_category_counts[primary_cat] = per_category_counts.get(primary_cat, 0) + 1

        repeated_harassment = any(count >= 2 for count in per_category_counts.values())
        threat_frequency = threat_labeled_count / total_messages if total_messages > 0 else 0.0

        # Escalation Detection
        if total_messages >= 10:
            mid = total_messages // 2
            first_half = analyzed_messages[:mid]
            second_half = analyzed_messages[mid:]
            
            first_half_avg = sum(m["risk_score"] for m in first_half) / len(first_half) if first_half else 0
            second_half_avg = sum(m["risk_score"] for m in second_half) / len(second_half) if second_half else 0
            
            has_high_severity_second_half = any(m["risk_score"] >= 70 for m in second_half)
            
            if second_half_avg > first_half_avg * 1.25 and has_high_severity_second_half:
                escalation_score = 40
                escalation_level = "High"
                escalation_reason.append(f"Macro escalation detected (First half avg: {first_half_avg:.1f}, Second half avg: {second_half_avg:.1f})")
            else:
                escalation_score = 0
                escalation_level = "None"
        else:
            # Fallback for < 10 messages: existing naive logic
            max_prev_risk = 0
            prev_categories = set()
            for msg in analyzed_messages:
                primary_cat = msg["prediction"].get("primary_label", "Clean")
                msg_risk = msg["risk_score"]
                
                if primary_cat != "Clean":
                    if primary_cat in prev_categories:
                        escalation_score += 15
                        escalation_reason.append(f"Repeated toxicity: {primary_cat}")
                    prev_categories.add(primary_cat)
                
                if msg_risk > max_prev_risk and max_prev_risk > 0 and msg_risk > 40:
                    diff = msg_risk - max_prev_risk
                    if diff > 20:
                        escalation_score += 25
                        escalation_reason.append(f"Severe escalation detected (Risk jumped by {round(diff, 1)})")
                    else:
                        escalation_score += 10
                        escalation_reason.append(f"Escalation detected (Risk increased)")
                max_prev_risk = max(max_prev_risk, msg_risk)
                
            if escalation_score >= 40:
                escalation_level = "High"
            elif escalation_score >= 15:
                escalation_level = "Medium"
            elif escalation_score > 0:
                escalation_level = "Low"

        # Add escalation score to conversation risk
        conversation_risk += (escalation_score * 0.5)
        conversation_risk = min(100.0, round(conversation_risk, 1))
            
        if not escalation_reason:
            escalation_reason = ["No significant escalation detected."]

        # Summarize the primary/secondary labels across the conversation
        all_labels = {}
        for msg in analyzed_messages:
            p = msg["prediction"]["primary_label"]
            if p != "Clean":
                all_labels[p] = max(all_labels.get(p, 0), msg["prediction"]["confidence"])
            for sec, sc_conf in msg["prediction"]["secondary_labels"].items():
                all_labels[sec] = max(all_labels.get(sec, 0), sc_conf)
                
        # Primary label of the conversation is the one with the highest confidence
        if all_labels:
            conv_primary = max(all_labels, key=all_labels.get)
            all_labels.pop(conv_primary)
            conv_secondary = all_labels
        else:
            conv_primary = "Clean"
            conv_secondary = {}

        return {
            "conversation_id": str(uuid.uuid4()),
            "messages": analyzed_messages,
            "escalation_level": escalation_level,
            "escalation_score": escalation_score,
            "escalation_reason": list(set(escalation_reason)), # Unique reasons
            "conversation_risk": conversation_risk,
            "primary_label": conv_primary,
            "secondary_labels": conv_secondary,
            "model": "conversation-adapter(" + analyzed_messages[-1]["prediction"]["model"] + ")" if analyzed_messages else "unknown",
            "total_messages": total_messages,
            "per_category_counts": per_category_counts,
            "high_risk_message_count": high_risk_message_count,
            "repeated_harassment": repeated_harassment,
            "threat_frequency": threat_frequency
        }
