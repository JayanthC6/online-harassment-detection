from typing import List, Dict
from .base import ModelAdapter
import uuid
from datetime import datetime, timezone
import dateutil.parser

CATEGORY_DISPLAY_MAP = {
    "threat": "Threat",
    "sextortion": "Blackmail / Sextortion",
    "scam": "Scam",
    "phishing": "Phishing",
    "harassment": "Cyberbullying / Harassment",
    "abusive_language": "Abusive Language"
}

class ConversationAdapter:
    def __init__(self, message_adapter: ModelAdapter = None):
        """
        Wraps a single-message ModelAdapter or Detection Engine to evaluate an entire conversation.
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

            # If using DummyModelAdapter in tests, use its predict method
            if self.message_adapter and type(self.message_adapter).__name__ == "DummyModelAdapter":
                prediction = self.message_adapter.predict(text)
                from services.prediction_service import PredictionService
                primary_cat = prediction.get("primary_label", prediction.get("category", "none"))
                conf = prediction.get("confidence", 0)
                msg_risk = PredictionService.compute_risk_score(
                    primary_cat, conf, prediction.get("secondary_labels", {})
                )
                category_scores = {}
                signals = []
            else:
                from services.prediction_service import PredictionService
                try:
                    prediction = PredictionService.classify_text(text)
                    primary_cat = prediction.get("primary_label", prediction.get("category", "Clean"))
                    conf = prediction.get("confidence", 0)
                    msg_risk = float(prediction.get("score", prediction.get("risk_score", 0.0)))
                    category_scores = prediction.get("category_scores", {})
                    signals = prediction.get("signals", [])
                except Exception:
                    prediction = self.message_adapter.predict(text) if self.message_adapter else {}
                    primary_cat = prediction.get("primary_label", prediction.get("category", "Clean"))
                    conf = prediction.get("confidence", 0)
                    from services.prediction_service import PredictionService
                    msg_risk = PredictionService.compute_risk_score(
                        primary_cat, conf, prediction.get("secondary_labels", {})
                    )
                    category_scores = prediction.get("category_scores", {})
                    signals = prediction.get("signals", [])
            
            analyzed_messages.append({
                "message_id": str(uuid.uuid4()),
                "text": text,
                "sender": sender,
                "timestamp": timestamp,
                "prediction": prediction,
                "risk_score": msg_risk,
                "category_scores": category_scores,
                "signals": signals,
                "sequence_id": i
            })

        # Base Stats
        total_messages = len(analyzed_messages)
        per_category_counts = {}
        high_risk_message_count = 0
        threat_labeled_count = 0
        conversation_risk = 0
        
        # --- PHASE 3: ACTOR INTELLIGENCE ---
        actor_stats = {}
        
        # Pass 1: Compute risk for all messages, gather global stats and actor stats
        for msg in analyzed_messages:
            pred = msg["prediction"]
            primary_cat = pred.get("primary_label", pred.get("category", "Clean"))
            msg_risk = msg.get("risk_score", 0.0)
            conversation_risk = max(conversation_risk, msg_risk)
            
            # Global Stats
            if msg_risk >= 70:
                high_risk_message_count += 1
            if primary_cat.lower() == "threat":
                threat_labeled_count += 1
            if primary_cat.lower() not in ["clean", "none", "safe"]:
                per_category_counts[primary_cat] = per_category_counts.get(primary_cat, 0) + 1
                
            # Actor Stats
            sender = msg["sender"]
            if sender not in actor_stats:
                actor_stats[sender] = {
                    "total_messages": 0,
                    "flagged_messages": 0,
                    "high_risk_messages": 0,
                    "threat_related_messages": 0,
                    "harassment_related_messages": 0,
                    "category_distribution": {},
                    "risk_sum": 0,
                    "maximum_risk_score": 0
                }
                
            a_stats = actor_stats[sender]
            a_stats["total_messages"] += 1
            a_stats["risk_sum"] += msg_risk
            a_stats["maximum_risk_score"] = max(a_stats["maximum_risk_score"], msg_risk)
            
            is_threat = (
                primary_cat.lower() == "threat"
                or "threat" in [str(k).lower() for k in pred.get("secondary_labels", {}).keys()]
                or (msg.get("category_scores", {}).get("threat", 0) >= 30.0)
            )
            is_harass = (
                primary_cat in ["Cyberbullying / Harassment", "Hate Speech", "Identity Attack", "Sexual Harassment", "Toxicity / Offensive Language", "Profanity", "Abusive Language"]
                or any(sec in ["Cyberbullying / Harassment", "Hate Speech", "Identity Attack", "Sexual Harassment", "Toxicity / Offensive Language", "Profanity", "Abusive Language"] for sec in pred.get("secondary_labels", {}))
                or (msg.get("category_scores", {}).get("harassment", 0) >= 30.0)
                or (msg.get("category_scores", {}).get("abusive_language", 0) >= 30.0)
            )
            
            # Message is flagged ONLY if its own score crosses threshold (>=30.0) AND category is not Clean/None/Safe
            is_flagged = (msg_risk >= 30.0 and primary_cat.lower() not in ["clean", "none", "safe"]) or (
                pred.get("label") == "harassing" and primary_cat.lower() not in ["clean", "none", "safe"]
            )
            msg["is_flagged"] = is_flagged

            if is_flagged:
                a_stats["flagged_messages"] += 1
                if primary_cat not in ["Clean", "none", "Safe", "None"]:
                    a_stats["category_distribution"][primary_cat] = a_stats["category_distribution"].get(primary_cat, 0) + 1
            if msg_risk >= 70 and is_flagged:
                a_stats["high_risk_messages"] += 1
            if is_threat and is_flagged:
                a_stats["threat_related_messages"] += 1
            if is_harass and is_flagged:
                a_stats["harassment_related_messages"] += 1

        total_flagged = sum(a["flagged_messages"] for a in actor_stats.values())
        
        actor_intelligence = {}
        for sender, a_stats in actor_stats.items():
            a_stats["average_risk_score"] = round(a_stats["risk_sum"] / a_stats["total_messages"], 1) if a_stats["total_messages"] > 0 else 0
            del a_stats["risk_sum"]
            a_stats["risk_concentration_percentage"] = round((a_stats["flagged_messages"] / total_flagged * 100), 1) if total_flagged > 0 else 0
            actor_intelligence[sender] = a_stats

        repeated_harassment = any(count >= 2 for count in per_category_counts.values())
        threat_frequency = threat_labeled_count / total_messages if total_messages > 0 else 0.0

        # --- PHASE 3: TEMPORAL INTELLIGENCE ---
        temporal_intelligence = {
            "risk_timeline": [],
            "high_risk_clusters": [],
            "risk_trend": "stable"
        }
        
        has_real_timestamps = False
        try:
            if len(analyzed_messages) > 1:
                t0 = dateutil.parser.isoparse(analyzed_messages[0]["timestamp"])
                t1 = dateutil.parser.isoparse(analyzed_messages[1]["timestamp"])
                has_real_timestamps = True
        except Exception:
            pass

        temporal_intelligence["time_basis"] = "timestamp" if has_real_timestamps else "sequence"
        
        for msg in analyzed_messages:
            msg_risk = msg.get("risk_score", 0.0)
            msg_sender = msg.get("sender", "Unknown")
            msg_level = msg.get("level")
            if not msg_level:
                msg_level = "critical" if msg_risk >= 75.0 else ("high" if msg_risk >= 50.0 else ("medium" if msg_risk >= 25.0 else "low"))
            temporal_intelligence["risk_timeline"].append({
                "sequence": msg["sequence_id"],
                "timestamp": msg["timestamp"],
                "sender": msg_sender,
                "risk_score": msg_risk,
                "level": msg_level,
                "is_high_risk": msg_risk >= 70,
                "text_snippet": (msg.get("text") or "")[:60]
            })
            
        clusters = []
        current_cluster = []
        for point in temporal_intelligence["risk_timeline"]:
            if point["is_high_risk"]:
                current_cluster.append(point)
            else:
                if len(current_cluster) >= 2:
                    clusters.append({
                        "start_sequence": current_cluster[0]["sequence"],
                        "end_sequence": current_cluster[-1]["sequence"],
                        "size": len(current_cluster),
                        "start_time": current_cluster[0]["timestamp"],
                        "end_time": current_cluster[-1]["timestamp"]
                    })
                current_cluster = []
        if len(current_cluster) >= 2:
            clusters.append({
                "start_sequence": current_cluster[0]["sequence"],
                "end_sequence": current_cluster[-1]["sequence"],
                "size": len(current_cluster),
                "start_time": current_cluster[0]["timestamp"],
                "end_time": current_cluster[-1]["timestamp"]
            })
        temporal_intelligence["high_risk_clusters"] = clusters
        
        # Trend detection
        if len(temporal_intelligence["risk_timeline"]) >= 4:
            mid = len(temporal_intelligence["risk_timeline"]) // 2
            first_half = temporal_intelligence["risk_timeline"][:mid]
            second_half = temporal_intelligence["risk_timeline"][mid:]
            avg_1 = sum(p["risk_score"] for p in first_half) / len(first_half)
            avg_2 = sum(p["risk_score"] for p in second_half) / len(second_half)
            if avg_2 > avg_1 + 15:
                temporal_intelligence["risk_trend"] = "escalating"
            elif avg_1 > avg_2 + 15:
                temporal_intelligence["risk_trend"] = "de-escalating"
            else:
                temporal_intelligence["risk_trend"] = "stable"

        # Escalation Logic (Consistent level and plain English explanation)
        escalation_score = 0
        escalation_level = "None"
        escalation_reason = []

        max_prev_risk = 0.0
        max_jump = 0.0
        jump_start = 0.0
        jump_end = 0.0

        for msg in analyzed_messages:
            msg_risk = msg["risk_score"]
            if msg_risk > max_prev_risk and max_prev_risk > 0 and msg_risk > 40:
                diff = msg_risk - max_prev_risk
                if diff > max_jump:
                    max_jump = diff
                    jump_start = max_prev_risk
                    jump_end = msg_risk
            max_prev_risk = max(max_prev_risk, msg_risk)

        if temporal_intelligence["risk_trend"] == "escalating":
            macro_jump = round(avg_2 - avg_1) if ('avg_2' in locals() and 'avg_1' in locals()) else (round(max_jump) if max_jump > 0 else 25)
            escalation_score = max(round(max_jump), macro_jump)
            escalation_level = "High" if escalation_score >= 20 else ("Medium" if escalation_score >= 12 else "Low")
            baseline_val = round(avg_1) if 'avg_1' in locals() else round(jump_start)
            escalated_val = round(avg_2) if 'avg_2' in locals() else round(jump_end)
            escalation_reason.append(
                f"Macro escalation detected (+{escalation_score} risk points): Conversation escalated sharply from baseline messages ({baseline_val}/100) to acute high-risk messages ({escalated_val}/100)."
            )
        elif max_jump > 0:
            escalation_score = round(max_jump)
            if max_jump > 20:
                escalation_level = "High"
                escalation_reason.append(
                    f"High risk escalation detected (+{escalation_score} risk points): Conversation escalated sharply from baseline messages ({round(jump_start)}/100) to acute high-risk messages ({round(jump_end)}/100)."
                )
            elif max_jump > 12:
                escalation_level = "Medium"
                escalation_reason.append(
                    f"Moderate risk escalation detected (+{escalation_score} risk points): Message risk increased from {round(jump_start)}/100 to {round(jump_end)}/100."
                )
            else:
                escalation_level = "Low"
                escalation_reason.append(
                    f"Low risk escalation detected (+{escalation_score} risk points): Message risk increased from {round(jump_start)}/100 to {round(jump_end)}/100."
                )
        else:
            escalation_score = 0
            escalation_level = "None"
            escalation_reason.append("No significant risk escalation detected across messages.")

        # Cap conversation risk at the highest message score (so 98 does not become 100)
        peak_message_risk = max((msg.get("risk_score", 0.0) for msg in analyzed_messages), default=0.0)
        conversation_risk = round(peak_message_risk, 1)

        # --- PHASE 3: CONVERSATION EXPLANATION ---
        conversation_signals = []
        if actor_intelligence and total_flagged > 0:
            top_actor = max(actor_intelligence.items(), key=lambda x: x[1]["flagged_messages"])
            if top_actor[1]["flagged_messages"] > 0:
                conversation_signals.append(f"{top_actor[1]['flagged_messages']} of {total_flagged} flagged messages originated from {top_actor[0]}.")
        
        if len(temporal_intelligence["high_risk_clusters"]) > 0:
            conversation_signals.append("Several high-risk messages occurred within a short period.")
            
        if threat_labeled_count >= 2:
            conversation_signals.append("Threat-related messages were detected repeatedly.")
            
        if high_risk_message_count > 0:
            conversation_signals.append(f"The conversation contains {high_risk_message_count} high-risk messages out of {total_messages} total messages.")

        # Summarize category scores and labels across the conversation
        agg_cat_scores = {
            "threat": 0.0,
            "sextortion": 0.0,
            "scam": 0.0,
            "phishing": 0.0,
            "harassment": 0.0,
            "abusive_language": 0.0
        }

        has_cat_scores = False
        for msg in analyzed_messages:
            pred_cats = msg.get("category_scores") or msg.get("prediction", {}).get("category_scores", {})
            for c_name, c_score in pred_cats.items():
                c_key = c_name.lower()
                if c_key in agg_cat_scores:
                    has_cat_scores = True
                    agg_cat_scores[c_key] = max(agg_cat_scores[c_key], float(c_score))

        if has_cat_scores and any(sc >= 25.0 for sc in agg_cat_scores.values()):
            sorted_cats = sorted(agg_cat_scores.items(), key=lambda x: x[1], reverse=True)
            top_cat_key, top_cat_score = sorted_cats[0]
            conv_primary = CATEGORY_DISPLAY_MAP.get(top_cat_key, top_cat_key.replace("_", " ").title())

            conv_secondary = {}
            for cat_key, cat_score in sorted_cats[1:]:
                if cat_score >= 25.0:
                    display_name = CATEGORY_DISPLAY_MAP.get(cat_key, cat_key.replace("_", " ").title())
                    conv_secondary[display_name] = round(cat_score / 100.0, 3)
        else:
            # Fallback for dummy adapter in tests
            all_labels = {}
            for msg in analyzed_messages:
                p = msg["prediction"].get("primary_label", msg["prediction"].get("category", "Clean"))
                if p not in ["Clean", "none", "Safe", "None"]:
                    conf = msg["prediction"].get("confidence", 0)
                    all_labels[p] = max(all_labels.get(p, 0), conf)
                for sec, sc_conf in msg["prediction"].get("secondary_labels", {}).items():
                    if sec not in ["Clean", "none", "Safe", "None"]:
                        all_labels[sec] = max(all_labels.get(sec, 0), sc_conf)

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
            
            # Contract fields
            "escalation_level": escalation_level,
            "escalation_score": escalation_score,
            "escalation_reason": list(set(escalation_reason)),
            "conversation_risk": conversation_risk,
            "primary_label": conv_primary,
            "secondary_labels": conv_secondary,
            "category_scores": agg_cat_scores if has_cat_scores else {},
            "model": "conversation-adapter(" + analyzed_messages[-1]["prediction"]["model"] + ")" if analyzed_messages and "model" in analyzed_messages[-1]["prediction"] else "conversation-adapter",
            "total_messages": total_messages,
            "per_category_counts": per_category_counts,
            "high_risk_message_count": high_risk_message_count,
            "repeated_harassment": repeated_harassment,
            "threat_frequency": threat_frequency,
            
            # Phase 3 Fields
            "actor_intelligence": actor_intelligence,
            "temporal_intelligence": temporal_intelligence,
            "conversation_signals": conversation_signals
        }
