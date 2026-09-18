import math 

class ConfidenceScorer:
    """Calculates confidence scores based on three independent factors:
    1. Source reliability (who said it)
    2. Freshness (when they said it)
    3. Statement clarity (how certain was the statement)
    """

    def __init__(self):
        self.source_reliability = {
            "official_site": 0.95,
            "academic": 0.90,
            "news": 0.80,
            "wikipedia": 0.65,
            "search_snippet": 0.50,
            "blog": 0.40,
            "reddit": 0.30,
            "unknown": 0.40
        }

        self.statement_clarity = {
            "exact": 0.95,
            "approximate": 0.70,
            "uncertain": 0.40
        }
        self.freshness_decay_k = 0.004



    def score_source(self, source_type: str) -> float:
        """Get base confidence for a source type (0.0 - 1.0)"""
        return self.source_reliability.get(source_type.lower(), 0.40)

    def get_extraction_certainty(self, statement_clarity: str) -> float:
        """Returns confidence based on how clear/unambiguous the statement is"""
        return self.statement_clarity.get(statement_clarity.lower(), 0.70)

    def get_freshness_multiplier(self, days_old: int) -> float:
        if days_old<0:
            raise ValueError("days cant be negative")
        needed=(-self.freshness_decay_k*days_old)
        return math.exp(needed)
        


    def calculate_confidence(self, source_type: str, days_old: int, statement_clarity: str) -> float:
        """Calculate final confidence by multiplying all three factors
        
        Formula: confidence = source_reliability × freshness × statement_clarity
        """
        source_conf = self.score_source(source_type)
        freshness_mult = self.get_freshness_multiplier(days_old)
        certainty_score = self.get_extraction_certainty(statement_clarity)

        final = source_conf * freshness_mult * certainty_score
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, final))

    def get_confidence_breakdown(self, source_type: str, days_old: int, statement_clarity: str) -> dict:
        """Returns detailed breakdown of confidence calculation"""
        source_conf = self.score_source(source_type)
        freshness_mult = self.get_freshness_multiplier(days_old)
        certainty_score = self.get_extraction_certainty(statement_clarity)
        final = self.calculate_confidence(source_type, days_old, statement_clarity)

        return {
            "final_confidence": final,
            "source_reliability": source_conf,
            "freshness_multiplier": freshness_mult,
            "statement_certainty": certainty_score,
            "breakdown": f"{source_conf} × {freshness_mult} × {certainty_score} = {final}"
        }