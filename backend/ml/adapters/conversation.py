from typing import List, Dict
from .base import ModelAdapter
import uuid
from datetime import datetime, timezone
import dateutil.parser

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
                "prediction": prediction,
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
            primary_cat = pred.get("primary_label", pred.get("category", "none"))
            conf = pred.get("confidence", 0)
            
            from services.prediction_service import PredictionService
            msg_risk = PredictionService.compute_risk_score(
                primary_cat, conf, pred.get("secondary_labels", {})
            )
            msg["risk_score"] = msg_risk
            conversation_risk = max(conversation_risk, msg_risk)
            
            # Global Stats
            if msg_risk >= 70:
                high_risk_message_count += 1
            if primary_cat == "Threat":
                threat_labeled_count += 1
            if primary_cat != "Clean":
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
            
            is_threat = primary_cat == "Threat" or "Threat" in pred.get("secondary_labels", {})
            is_harass = primary_cat in ["Cyberbullying / Harassment", "Hate Speech", "Identity Attack", "Sexual Harassment", "Toxicity / Offensive Language", "Profanity"] or any(sec in ["Cyberbullying / Harassment", "Hate Speech", "Identity Attack", "Sexual Harassment", "Toxicity / Offensive Language", "Profanity"] for sec in pred.get("secondary_labels", {}))
            
            if msg_risk > 0 or primary_cat != "Clean":
                a_stats["flagged_messages"] += 1
            if msg_risk >= 70:
                a_stats["high_risk_messages"] += 1
            if is_threat:
                a_stats["threat_related_messages"] += 1
            if is_harass:
                a_stats["harassment_related_messages"] += 1
                
            if primary_cat != "Clean":
                a_stats["category_distribution"][primary_cat] = a_stats["category_distribution"].get(primary_cat, 0) + 1

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
            # Check if timestamps are actual datetimes
            if len(analyzed_messages) > 1:
                t0 = dateutil.parser.isoparse(analyzed_messages[0]["timestamp"])
                t1 = dateutil.parser.isoparse(analyzed_messages[1]["timestamp"])
                has_real_timestamps = True
        except Exception:
            pass

        temporal_intelligence["time_basis"] = "timestamp" if has_real_timestamps else "sequence"
        
        for msg in analyzed_messages:
            temporal_intelligence["risk_timeline"].append({
                "sequence": msg["sequence_id"],
                "timestamp": msg["timestamp"],
                "risk_score": msg["risk_score"],
                "is_high_risk": msg["risk_score"] >= 70
            })
            
        # Cluster detection (e.g. 3 high risk messages within 5 messages sequence)
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

        # Escalation Logic (Preserving old contract variables)
        escalation_score = 0
        escalation_level = "None"
        escalation_reason = []
        
        if temporal_intelligence["risk_trend"] == "escalating":
            escalation_score = 40
            escalation_level = "High"
            escalation_reason.append("Macro escalation detected in risk trend.")
        else:
            # Fallback naive logic
            max_prev_risk = 0
            for msg in analyzed_messages:
                msg_risk = msg["risk_score"]
                if msg_risk > max_prev_risk and max_prev_risk > 0 and msg_risk > 40:
                    diff = msg_risk - max_prev_risk
                    if diff > 20:
                        escalation_score += 25
                        escalation_reason.append(f"Severe escalation detected (Risk jumped by {round(diff, 1)})")
                    else:
                        escalation_score += 10
                        escalation_reason.append("Escalation detected (Risk increased)")
                max_prev_risk = max(max_prev_risk, msg_risk)
            
            if escalation_score >= 40:
                escalation_level = "High"
            elif escalation_score >= 15:
                escalation_level = "Medium"
            elif escalation_score > 0:
                escalation_level = "Low"

        conversation_risk += (escalation_score * 0.5)
        conversation_risk = min(100.0, round(conversation_risk, 1))
        
        if not escalation_reason:
            escalation_reason = ["No significant escalation detected."]

        # --- PHASE 3: CONVERSATION EXPLANATION ---
        conversation_signals = []
        # Find actor with most flagged
        if actor_intelligence and total_flagged > 0:
            top_actor = max(actor_intelligence.items(), key=lambda x: x[1]["flagged_messages"])
            if top_actor[1]["flagged_messages"] > 0:
                conversation_signals.append(f"{top_actor[1]['flagged_messages']} of {total_flagged} flagged messages originated from one actor.")
        
        if len(temporal_intelligence["high_risk_clusters"]) > 0:
            conversation_signals.append("Several high-risk messages occurred within a short period.")
            
        if threat_labeled_count >= 2:
            conversation_signals.append("Threat-related messages were detected repeatedly.")
            
        if high_risk_message_count > 0:
            conversation_signals.append(f"The conversation contains {high_risk_message_count} high-risk messages out of {total_messages} total messages.")

        # Summarize the primary/secondary labels across the conversation
        all_labels = {}
        for msg in analyzed_messages:
            p = msg["prediction"]["primary_label"]
            if p != "Clean":
                all_labels[p] = max(all_labels.get(p, 0), msg["prediction"]["confidence"])
            for sec, sc_conf in msg["prediction"]["secondary_labels"].items():
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
            
            # Old fields preserved
            "escalation_level": escalation_level,
            "escalation_score": escalation_score,
            "escalation_reason": list(set(escalation_reason)),
            "conversation_risk": conversation_risk,
            "primary_label": conv_primary,
            "secondary_labels": conv_secondary,
            "model": "conversation-adapter(" + analyzed_messages[-1]["prediction"]["model"] + ")" if analyzed_messages else "unknown",
            "total_messages": total_messages,
            "per_category_counts": per_category_counts,
            "high_risk_message_count": high_risk_message_count,
            "repeated_harassment": repeated_harassment,
            "threat_frequency": threat_frequency,
            
            # New Phase 3 Fields
            "actor_intelligence": actor_intelligence,
            "temporal_intelligence": temporal_intelligence,
            "conversation_signals": conversation_signals
        }
