"""
Week 7: Cost Optimization & Feedback Loop Starter Template

Implement three systems:
1. CostAnalyzer - analyze and track query costs
2. OptimizationStrategy - optimize costs through caching, model selection, etc.
3. FeedbackLoop - collect and validate user corrections
"""

import json
import logging
import statistics
from collections import Counter
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# TASK 1: Implement CostAnalyzer
# ============================================================================


class CostAnalyzer:
    """Analyze and track query costs by component."""

    def __init__(self):
        """Initialize cost analyzer.

        TODO: Initialize empty query history list
        """
        self.query_history = []

    def record_query(self, query: Dict[str, Any]):
        """Record a query and its cost breakdown.

        TODO: Store query dict with fields:
        - query_text: the user's question
        - retrieval_cost: cost of retrieving documents
        - llm_cost: cost of LLM inference
        - tool_cost: cost of tool calls
        - error_cost: cost of retries/errors
        - total_cost: sum of above
        - timestamp: when query was run (use datetime.utcnow().isoformat())
        """
        query["timestamp"] = datetime.utcnow().isoformat()
        if "total_cost" not in query:
            query["total_cost"] = (
                query.get("retrieval_cost", 0.0)
                + query.get("llm_cost", 0.0)
                + query.get("tool_cost", 0.0)
                + query.get("error_cost", 0.0)
            )
        self.query_history.append(query)

    def get_cost_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of costs by component.

        TODO: Calculate totals for all queries:
        - retrieval_total
        - llm_total
        - tool_total
        - error_total
        - total_daily (sum of all)
        - query_count

        Return dict with these totals
        """
        retrieval_total = sum(q.get("retrieval_cost", 0.0) for q in self.query_history)
        llm_total = sum(q.get("llm_cost", 0.0) for q in self.query_history)
        tool_total = sum(q.get("tool_cost", 0.0) for q in self.query_history)
        error_total = sum(q.get("error_cost", 0.0) for q in self.query_history)
        return {
            "retrieval_total": retrieval_total,
            "llm_total": llm_total,
            "tool_total": tool_total,
            "error_total": error_total,
            "total_daily": retrieval_total + llm_total + tool_total + error_total,
            "query_count": len(self.query_history),
        }

    def identify_cost_spikes(self) -> List[Dict]:
        """Identify unusually expensive queries.

        TODO: Find statistical outliers:
        1. Calculate mean and standard deviation of query costs
        2. Find queries > mean + 2*stdev
        3. Return list of spike queries with details
        """
        if len(self.query_history) < 2:
            return []
        costs = [q.get("total_cost", 0.0) for q in self.query_history]
        mean = statistics.mean(costs)
        stdev = statistics.stdev(costs)
        threshold = mean + 2 * stdev
        return [q for q in self.query_history if q.get("total_cost", 0.0) > threshold]


# ============================================================================
# TASK 2: Implement OptimizationStrategy
# ============================================================================


class OptimizationStrategy:
    """Optimize agent costs through multiple strategies."""

    def __init__(self):
        """Initialize optimization strategy.

        TODO: Initialize cache and strategy tracking
        """
        self.cache = {}  # {query: response}
        self.strategies_applied = []

    def apply_caching(self, query: str, response: str) -> tuple:
        """Cache query responses.

        TODO: Implement caching
        1. If query in cache, return (True, cached_response)
        2. Otherwise, store in cache and return (False, response)

        Args:
            query: user's question
            response: LLM's answer

        Returns:
            (is_cached_hit, response)
        """
        if query in self.cache:
            if "caching" not in self.strategies_applied:
                self.strategies_applied.append("caching")
            return (True, self.cache[query])
        self.cache[query] = response
        return (False, response)

    def optimize_retrieval_count(self, num_docs: int) -> int:
        """Reduce number of documents retrieved.

        TODO: Reduce count intelligently
        - Input 15 docs → output 3 docs (top-k)
        - Reduces token cost

        Args:
            num_docs: original document count

        Returns:
            optimized document count
        """
        if "retrieval_optimization" not in self.strategies_applied:
            self.strategies_applied.append("retrieval_optimization")
        return max(1, num_docs // 5)  # Simple: reduce by 5x

    def select_model_by_complexity(self, query: str) -> str:
        """Choose cheaper model for simple queries.

        TODO: Analyze query complexity
        - Simple queries ("What is X?") → gemini-1.5-flash (cheaper, faster)
        - Complex queries ("Analyze...", "Compare...", "Design...") → gemini-2.5-pro

        Args:
            query: user's question

        Returns:
            model name to use
        """
        complex_keywords = ["analyze", "compare", "design", "evaluate", "synthesize", "contrast"]
        if any(kw in query.lower() for kw in complex_keywords):
            if "model_selection" not in self.strategies_applied:
                self.strategies_applied.append("model_selection")
            return "gemini-2.5-flash"
        return "gemini-2.5-flash-lite"

    def enable_response_compression(self, response: str) -> str:
        """Compress long responses while keeping essential info.

        TODO: Reduce response length
        1. Split into sentences
        2. Keep only first N essential sentences
        3. Return compressed response

        Args:
            response: original response

        Returns:
            compressed response
        """
        sentences = [s.strip() for s in response.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        compressed = ". ".join(sentences[:3])
        if compressed and not compressed.endswith("."):
            compressed += "."
        if "compression" not in self.strategies_applied:
            self.strategies_applied.append("compression")
        return compressed

    def get_optimization_impact(self) -> Dict[str, Any]:
        """Estimate cost savings from applied optimizations.

        TODO: Return impact analysis:
        - total_savings_pct: estimated % cost reduction
        - strategies_applied: list of which strategies used
        - breakdown: savings estimate per strategy
        """
        savings_per_strategy = {
            "caching": 100.0,
            "retrieval_optimization": 80.0,
            "model_selection": 50.0,
            "compression": 20.0,
        }
        breakdown = {s: savings_per_strategy[s] for s in self.strategies_applied if s in savings_per_strategy}
        total_savings = sum(breakdown.values()) / len(breakdown) if breakdown else 0.0
        return {
            "total_savings_pct": total_savings,
            "strategies_applied": self.strategies_applied,
            "breakdown": breakdown,
        }


# ============================================================================
# TASK 3: Implement FeedbackLoop
# ============================================================================


class FeedbackLoop:
    """Collect and validate user corrections for continuous improvement."""

    def __init__(self):
        """Initialize feedback loop.

        TODO: Initialize corrections list and validation rules
        """
        self.corrections = []
        # Authority hierarchy for role-based validation
        self.authority = {
            "engineer": 1,
            "hr": 2,
            "finance": 2,
            "manager": 3,
            "executive": 4,
        }

    def submit_correction(
        self,
        original_query: str,
        original_answer: str,
        corrected_answer: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Submit a correction to the agent's answer.

        TODO: Validate and store correction
        1. Check user_role has sufficient authority
        2. Check corrected_answer is detailed enough (longer than original)
        3. Store in corrections list
        4. Return acceptance status

        Args:
            original_query: the question
            original_answer: agent's incorrect answer
            corrected_answer: user's correction
            user_role: user's role (for authority check)

        Returns:
            {"accepted": True/False, "reason": "..."}
        """
        if user_role not in self.authority:
            return {"accepted": False, "reason": f"Unknown role: {user_role}"}
        if len(corrected_answer) <= len(original_answer):
            return {"accepted": False, "reason": "Correction must be more detailed than original answer"}
        self.corrections.append({
            "original_query": original_query,
            "user_role": user_role,
            "original_answer": original_answer,
            "corrected_answer": corrected_answer,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return {"accepted": True, "reason": "Correction accepted"}

    def validate_correction(self, index: int) -> bool:
        """Validate a stored correction is accurate.

        TODO: Check correction quality:
        1. User role has sufficient authority (manager+, i.e. level 3 or above)
        2. Correction is more detailed than original
        3. Correction makes sense

        Args:
            index: index into corrections list

        Returns:
            True if correction is valid, False otherwise
        """
        if index < 0 or index >= len(self.corrections):
            return False
        correction = self.corrections[index]
        if self.authority.get(correction.get("user_role", ""), 0) < 3:
            return False
        if len(correction.get("corrected_answer", "")) <= len(correction.get("original_answer", "")):
            return False
        if not correction.get("corrected_answer", "").strip():
            return False
        return True

    def get_feedback_metrics(self) -> Dict[str, Any]:
        """Compute metrics on feedback quality.

        TODO: Calculate:
        - total_corrections: number of corrections received
        - validation_rate: % of corrections that are valid
        - avg_correction_length: average length of corrections
        - top_error_patterns: most common mistakes corrected

        Returns:
            dict with feedback metrics
        """
        total = len(self.corrections)
        if total == 0:
            return {
                "total_corrections": 0,
                "validation_rate": 0.0,
                "avg_correction_length": 0.0,
                "top_error_patterns": [],
            }
        valid_count = sum(1 for i in range(total) if self.validate_correction(i))
        avg_length = sum(len(c.get("corrected_answer", "")) for c in self.corrections) / total
        words = []
        for c in self.corrections:
            words.extend(c.get("original_answer", "").lower().split())
        top_patterns = [word for word, _ in Counter(words).most_common(3)]
        return {
            "total_corrections": total,
            "validation_rate": valid_count / total,
            "avg_correction_length": avg_length,
            "top_error_patterns": top_patterns,
        }


if __name__ == "__main__":
    # Basic structure is provided below. Add your own test cases to verify your implementation.
    # Run with: python3 cost_optimization_starter.py

    # Test CostAnalyzer
    print("Testing CostAnalyzer")
    analyzer = CostAnalyzer()
    # TODO: record a query and verify get_cost_breakdown() returns correct totals
    for _ in range(8):
        analyzer.record_query({"query_text": "What is the travel policy?", "retrieval_cost": 0.001, "llm_cost": 0.004, "tool_cost": 0.0, "error_cost": 0.0, "total_cost": 0.005})
    analyzer.record_query({"query_text": "Analyze all employee compensation data", "retrieval_cost": 0.01, "llm_cost": 0.05, "tool_cost": 0.005, "error_cost": 0.002, "total_cost": 0.500})
    breakdown = analyzer.get_cost_breakdown()
    assert breakdown["query_count"] == 9, "Query count should be 9"
    assert breakdown["total_daily"] > 0, "Total daily cost should be > 0"
    assert breakdown["llm_total"] > 0, "LLM total should be > 0"
    print("  get_cost_breakdown: PASSED")
    spikes = analyzer.identify_cost_spikes()
    assert len(spikes) == 1, "Should detect 1 spike"
    assert spikes[0]["query_text"] == "Analyze all employee compensation data", "Wrong spike detected"
    print("identify_cost_spikes: PASSED")

    # Test OptimizationStrategy
    print("\nTesting OptimizationStrategy")
    optimizer = OptimizationStrategy()
    # TODO: test apply_caching, select_model_by_complexity, and optimize_retrieval_count
    is_hit, resp = optimizer.apply_caching("What is the PTO policy?", "You get 15 days PTO.")
    assert not is_hit, "First call should be a cache miss"
    is_hit, cached = optimizer.apply_caching("What is the PTO policy?", "")
    assert is_hit and cached == "You get 15 days PTO.", "Second call should be a cache hit"
    print("apply_caching: PASSED")
    simple_model = optimizer.select_model_by_complexity("What is the travel policy?")
    complex_model = optimizer.select_model_by_complexity("Analyze the compensation structure across all departments")
    assert simple_model != complex_model, "Simple and complex queries should use different models"
    assert complex_model == "gemini-2.5-flash", "Complex query should use gemini-2.5-flash"
    print("select_model_by_complexity: PASSED")
    assert optimizer.optimize_retrieval_count(15) == 3, "15 docs should reduce to 3"
    assert optimizer.optimize_retrieval_count(5) == 1, "5 docs should reduce to 1"
    print("optimize_retrieval_count: PASSED")

    # Test FeedbackLoop
    print("\nTesting FeedbackLoop")
    feedback = FeedbackLoop()
    # TODO: submit corrections with different roles and verify accepted/rejected correctly
    result = feedback.submit_correction(
        "What is the travel policy?",
        "No specific policy.",
        "All business travel requires manager pre-approval and must comply with the TechCorp Travel and Expense Policy, including per diem limits.",
        "engineer",
    )
    assert result["accepted"], "Engineer with longer correction should be accepted"
    print("submit_correction (engineer, valid): PASSED")
    result = feedback.submit_correction(
        "What is the PTO policy?",
        "You get some days off per year.",
        "15 days.",
        "manager",
    )
    assert not result["accepted"], "Shorter correction should be rejected"
    print("submit_correction (shorter correction rejected): PASSED")
    result = feedback.submit_correction(
        "What is the expense limit for a director?",
        "Directors have no limit.",
        "Directors have an expense approval limit of $25,000 per the TechCorp expense policy, requiring VP approval above that threshold.",
        "manager",
    )
    assert result["accepted"], "Manager with longer correction should be accepted"
    print("submit_correction (manager, valid): PASSED")
    assert not feedback.validate_correction(0), "Engineer correction should fail validation (authority < 3)"
    assert feedback.validate_correction(1), "Manager correction should pass validation"
    print("validate_correction: PASSED")
    metrics = feedback.get_feedback_metrics()
    assert metrics["total_corrections"] == 2, "Should have 2 stored corrections"
    assert metrics["validation_rate"] == 0.5, "1 of 2 corrections should be valid"
    print("get_feedback_metrics: PASSED")
    print("\nAll tests passed!")
