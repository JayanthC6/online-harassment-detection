def calculate_behavior_score(profile_stats):
    """
    Calculates the Behavioral Score (0-100) incrementally based on profile statistics.
    Returns: (score, level, recommendation, explanation)
    """
    avg_risk = profile_stats.get('avg_risk', 0.0)
    harmful_count = profile_stats.get('harmful_messages', 0)
    highest_risk = profile_stats.get('highest_risk', 0)
    categories = profile_stats.get('multi_label_distribution', {})
    total_messages = profile_stats.get('total_reports', 0)
    
    # 1. Base Score is the average risk
    score = avg_risk
    explanation = [f"Base score set by average risk: {avg_risk:.1f}"]
    
    # 2. Harmful volume penalty
    if harmful_count > 0:
        penalty = min(30, harmful_count * 5)
        score += penalty
        explanation.append(f"+{penalty} for repeated harmful behavior ({harmful_count} incidents).")
    
    # 3. Severity penalty
    if highest_risk >= 80:
        score += 15
        explanation.append("+15 for severe peak behavior (critical incident).")
    elif highest_risk >= 60:
        score += 5
        explanation.append("+5 for significant peak behavior (high risk incident).")
        
    # 4. Multi-label diversity / Severe Categories penalty
    severe_cats = sum(1 for c, count in categories.items() if c in ['Threat', 'Hate Speech', 'Cyberbullying'] and count > 0)
    if severe_cats > 0:
        penalty = severe_cats * 5
        score += penalty
        explanation.append(f"+{penalty} for engaging in severe categories ({severe_cats} types).")
        
    if len(categories) > 2:
        score += 10
        explanation.append("+10 for behavioral diversity (multiple attack vectors).")
        
    # Cap score
    score = min(100.0, max(0.0, score))
    
    # Determine Level and Recommendation
    if score >= 85:
        level = "Critical"
        recommendation = "Immediate Review Required / Permanent Ban"
    elif score >= 60:
        level = "High"
        recommendation = "Temporary Restriction / Final Warning"
    elif score >= 30:
        level = "Watch"
        recommendation = "Monitor User"
    else:
        level = "Normal"
        recommendation = "No action required"
        
    if total_messages > 0 and harmful_count == 0 and score < 30:
        explanation.append("User consistently exhibits safe behavior.")

    return score, level, recommendation, explanation
