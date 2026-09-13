#!/usr/bin/env python3
"""Tests for sentiment analysis."""

import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSentimentAnalysis:
    """Tests for VADER sentiment analysis."""

    def test_vader_available(self):
        """Test that VADER is available."""
        try:
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            analyzer = SentimentIntensityAnalyzer()
            assert analyzer is not None
        except ImportError:
            pytest.skip("NLTK not installed")

    def test_positive_sentiment(self):
        """Test positive text classification."""
        pytest.importorskip("nltk")
        
        from transformations.sentiment_analysis import analyze_sentiment
        
        sentiment, score = analyze_sentiment("Excellent service! Loved it!")
        
        assert sentiment in ["POSITIVE", "NEUTRAL"]
        assert -1.0 <= score <= 1.0

    def test_negative_sentiment(self):
        """Test negative text classification."""
        pytest.importorskip("nltk")
        
        from transformations.sentiment_analysis import analyze_sentiment
        
        sentiment, score = analyze_sentiment("Terrible experience, never again!")
        
        assert sentiment in ["NEGATIVE", "NEUTRAL"]
        assert -1.0 <= score <= 1.0

    def test_neutral_sentiment(self):
        """Test neutral text classification."""
        pytest.importorskip("nltk")
        
        from transformations.sentiment_analysis import analyze_sentiment
        
        sentiment, score = analyze_sentiment("Service was okay.")
        
        assert -1.0 <= score <= 1.0

    def test_empty_text(self):
        """Test with empty text."""
        pytest.importorskip("nltk")
        
        from transformations.sentiment_analysis import analyze_sentiment
        
        sentiment, score = analyze_sentiment("")
        
        assert sentiment == "NEUTRAL"
        assert score == 0.0

    def test_none_text(self):
        """Test with None text."""
        pytest.importorskip("nltk")
        
        from transformations.sentiment_analysis import analyze_sentiment
        
        sentiment, score = analyze_sentiment(None)
        
        assert sentiment == "NEUTRAL"
        assert score == 0.0

    def test_dataframe_analysis(self):
        """Test sentiment analysis on DataFrame."""
        pytest.importorskip("nltk")
        
        from transformations.sentiment_analysis import analyze_dataframe
        
        data = {
            "review_id": ["REV001", "REV002", "REV003"],
            "review_text": [
                "Excellent service! Loved it!",
                "Terrible experience, never again!",
                "Service was okay.",
            ],
        }
        df = pd.DataFrame(data)
        
        df_result = analyze_dataframe(df, text_column="review_text")
        
        assert "sentiment" in df_result.columns
        assert "sentiment_score" in df_result.columns
        assert len(df_result) == 3

    def test_sentiment_breakdown(self):
        """Test sentiment breakdown statistics."""
        pytest.importorskip("nltk")
        
        from transformations.sentiment_analysis import analyze_dataframe, get_sentiment_breakdown
        
        data = {
            "review_id": ["REV001", "REV002", "REV003"],
            "review_text": ["Great!", "Bad!", "Good."],
        }
        df = pd.DataFrame(data)
        
        df_result = analyze_dataframe(df)
        breakdown = get_sentiment_breakdown(df_result)
        
        assert "POSITIVE" in breakdown
        assert "NEUTRAL" in breakdown
        assert "NEGATIVE" in breakdown
