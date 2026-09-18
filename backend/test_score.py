from confidence_scorer import ConfidenceScorer

scorer = ConfidenceScorer()

# Test
result = scorer.get_confidence_breakdown("news", 30, "approximate")
print(result)