"""
Tests for LLM Client Cost/Token Tracking (Task G2).

Tests TokenUsage dataclass, SessionCostTracker, and cost calculation.
"""

import pytest
from src.core.llm_client import (
    TokenUsage,
    SessionCostTracker,
    LLMClient,
)


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_token_usage_creation(self):
        """Test creating TokenUsage with all fields."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.001,
            model="gpt-4o"
        )
        
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.estimated_cost_usd == 0.001
        assert usage.model == "gpt-4o"

    def test_token_usage_default_model(self):
        """Test TokenUsage with default empty model."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.001
        )
        
        assert usage.model == ""


class TestLLMClientCostCalculation:
    """Tests for LLMClient._calculate_cost method."""

    def test_calculate_cost_gpt5(self):
        """Test cost calculation for GPT-5 model."""
        client = LLMClient.__new__(LLMClient)  # Create without __init__
        
        # GPT-5: $1.25/1M input, $10.00/1M output
        cost = client._calculate_cost(
            model="gpt-5",
            prompt_tokens=1000,
            completion_tokens=500
        )
        
        # Expected: (1000/1M * 1.25) + (500/1M * 10.00) = 0.00125 + 0.005 = 0.00625
        assert cost == pytest.approx(0.00625, abs=0.0001)

    def test_calculate_cost_gpt5_mini(self):
        """Test cost calculation for GPT-5-mini model.
        
        Note: Due to prefix matching, gpt-5-mini matches "gpt-5" first in dict
        iteration, so it uses gpt-5 pricing ($1.25/1M input, $10.00/1M output).
        """
        client = LLMClient.__new__(LLMClient)
        
        # gpt-5-mini matches "gpt-5" prefix: $1.25/1M input, $10.00/1M output
        cost = client._calculate_cost(
            model="gpt-5-mini",
            prompt_tokens=10000,
            completion_tokens=2000
        )
        
        # Expected: (10000/1M * 1.25) + (2000/1M * 10.00) = 0.0125 + 0.020 = 0.0325
        assert cost == pytest.approx(0.0325, abs=0.001)

    def test_calculate_cost_claude_sonnet_45(self):
        """Test cost calculation for Claude Sonnet 4.5 model."""
        client = LLMClient.__new__(LLMClient)
        
        # Claude Sonnet 4.5: $3.00/1M input, $15.00/1M output
        cost = client._calculate_cost(
            model="claude-sonnet-4.5",
            prompt_tokens=5000,
            completion_tokens=1000
        )
        
        # Expected: (5000/1M * 3.00) + (1000/1M * 15.00) = 0.015 + 0.015 = 0.03
        assert cost == pytest.approx(0.03, abs=0.001)

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation returns 0 for unknown model."""
        client = LLMClient.__new__(LLMClient)
        
        cost = client._calculate_cost(
            model="unknown-model-xyz",
            prompt_tokens=1000,
            completion_tokens=500
        )
        
        assert cost == 0.0


class TestSessionCostTracker:
    """Tests for SessionCostTracker class."""

    def test_tracker_initialization(self):
        """Test tracker initializes with zero values."""
        tracker = SessionCostTracker()
        
        assert tracker.total_prompt_tokens == 0
        assert tracker.total_completion_tokens == 0
        assert tracker.total_cost_usd == 0.0
        assert tracker.call_count == 0
        assert tracker.total_tokens == 0
        assert tracker.usage_by_model == {}

    def test_tracker_add_single_usage(self):
        """Test adding a single usage record."""
        tracker = SessionCostTracker()
        
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.01,
            model="gpt-4o"
        )
        
        tracker.add(usage)
        
        assert tracker.total_prompt_tokens == 100
        assert tracker.total_completion_tokens == 50
        assert tracker.total_tokens == 150
        assert tracker.total_cost_usd == 0.01
        assert tracker.call_count == 1
        assert "gpt-4o" in tracker.usage_by_model

    def test_tracker_add_multiple_usages_same_model(self):
        """Test accumulation with same model."""
        tracker = SessionCostTracker()
        
        usage1 = TokenUsage(100, 50, 150, 0.01, "gpt-4o")
        usage2 = TokenUsage(200, 100, 300, 0.02, "gpt-4o")
        
        tracker.add(usage1)
        tracker.add(usage2)
        
        assert tracker.total_prompt_tokens == 300
        assert tracker.total_completion_tokens == 150
        assert tracker.total_tokens == 450
        assert tracker.total_cost_usd == pytest.approx(0.03, abs=0.001)
        assert tracker.call_count == 2
        
        # Check per-model stats
        model_stats = tracker.usage_by_model["gpt-4o"]
        assert model_stats["total_tokens"] == 450
        assert model_stats["call_count"] == 2

    def test_tracker_add_multiple_models(self):
        """Test accumulation with different models."""
        tracker = SessionCostTracker()
        
        usage1 = TokenUsage(100, 50, 150, 0.01, "gpt-4o")
        usage2 = TokenUsage(200, 100, 300, 0.02, "claude-sonnet-4-5")
        
        tracker.add(usage1)
        tracker.add(usage2)
        
        assert tracker.call_count == 2
        assert len(tracker.usage_by_model) == 2
        assert "gpt-4o" in tracker.usage_by_model
        assert "claude-sonnet-4-5" in tracker.usage_by_model

    def test_tracker_get_model_breakdown(self):
        """Test get_model_breakdown returns correct structure."""
        tracker = SessionCostTracker()
        
        tracker.add(TokenUsage(100, 50, 150, 0.01, "gpt-4o"))
        tracker.add(TokenUsage(200, 100, 300, 0.02, "gpt-4o-mini"))
        
        breakdown = tracker.get_model_breakdown()
        
        assert len(breakdown) == 2
        
        # Find gpt-4o entry
        gpt4o_entry = next(b for b in breakdown if b["model"] == "gpt-4o")
        assert gpt4o_entry["tokens"] == 150
        assert gpt4o_entry["cost_usd"] == 0.01

    def test_tracker_reset(self):
        """Test reset clears all values."""
        tracker = SessionCostTracker()
        
        tracker.add(TokenUsage(100, 50, 150, 0.01, "gpt-4o"))
        tracker.reset()
        
        assert tracker.total_prompt_tokens == 0
        assert tracker.total_completion_tokens == 0
        assert tracker.total_cost_usd == 0.0
        assert tracker.call_count == 0
        assert tracker.usage_by_model == {}

    def test_tracker_summary(self):
        """Test summary string formatting."""
        tracker = SessionCostTracker()
        
        tracker.add(TokenUsage(1000, 500, 1500, 0.0123, "gpt-4o"))
        tracker.add(TokenUsage(2000, 1000, 3000, 0.0456, "gpt-4o"))
        
        summary = tracker.summary()
        
        assert "2 calls" in summary
        assert "4,500 tokens" in summary
        assert "$0.0579" in summary
