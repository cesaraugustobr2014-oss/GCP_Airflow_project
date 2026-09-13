#!/usr/bin/env python3
"""
Sentiment analysis module using VADER.

This module provides functions to analyze the sentiment of customer reviews.
VADER (Valence Aware Dictionary and sEntiment Reasoner) is a rule-based model
specifically designed for social media and customer feedback data.

Sentiment Categories:
- POSITIVE: sentiment_score >= 0.5
- NEUTRAL: -0.5 < sentiment_score < 0.5
- NEGATIVE: sentiment_score <= -0.5
"""

import logging
from typing import Tuple, Union
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    nltk_available = True
except ImportError:
    nltk_available = False
    logger.warning("NLTK not installed. Install with: pip install nltk")

_analyzer_instance = None

# Portuguese sentiment lexicon additions to support PT-BR reviews alongside English
PORTUGUESE_LEXICON = {
    "excelente": 3.0, "incrivel": 3.0, "incrível": 3.0, "otimo": 2.8, "ótimo": 2.8,
    "otima": 2.8, "ótima": 2.8, "adoramos": 2.5, "adorei": 2.5, "perfeito": 3.0,
    "maravilhoso": 3.0, "maravilhosa": 3.0, "satisfeito": 2.2, "superou": 2.4,
    "profissional": 2.0, "atenciosa": 2.0, "atencioso": 2.0, "recomendar": 2.0,
    "recomendo": 2.2, "bom": 1.5, "boa": 1.5, "obrigado": 1.5,
    "pessimo": -3.2, "péssimo": -3.2, "pessima": -3.2, "péssima": -3.2,
    "ruim": -2.5, "horrivel": -3.0, "horrível": -3.0, "demorou": -1.8,
    "problema": -2.0, "problemas": -2.0, "defeito": -2.2, "descuidado": -2.0,
    "decepcionado": -2.5, "decepcionante": -2.5, "nunca": -1.5, "falha": -2.0,
}


def _get_analyzer() -> SentimentIntensityAnalyzer:
    """Get or create singleton VADER analyzer with Portuguese lexicon extensions."""
    global _analyzer_instance
    if _analyzer_instance is None:
        analyzer = SentimentIntensityAnalyzer()
        analyzer.lexicon.update(PORTUGUESE_LEXICON)
        _analyzer_instance = analyzer
    return _analyzer_instance


def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyze sentiment of a single text.
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (sentiment_label, sentiment_score)
        - sentiment_label: "POSITIVE", "NEUTRAL", or "NEGATIVE"
        - sentiment_score: VADER compound score (-1.0 to +1.0)
    """
    if not nltk_available:
        raise ImportError("NLTK is required. Install with: pip install nltk")
    
    if text is None or str(text).strip() == "":
        return "NEUTRAL", 0.0
    
    analyzer = _get_analyzer()
    
    # Get sentiment scores
    scores = analyzer.polarity_scores(str(text))
    compound_score = scores["compound"]
    
    # Determine sentiment label
    if compound_score >= 0.5:
        sentiment = "POSITIVE"
    elif compound_score <= -0.5:
        sentiment = "NEGATIVE"
    else:
        sentiment = "NEUTRAL"
    
    return sentiment, compound_score


def analyze_dataframe(df: pd.DataFrame, text_column: str = "review_text") -> pd.DataFrame:
    """
    Analyze sentiment for a DataFrame of reviews.
    
    Args:
        df: Input DataFrame with reviews
        text_column: Column name containing review text
        
    Returns:
        DataFrame with added sentiment columns
    """
    if not nltk_available:
        raise ImportError("NLTK is required. Install with: pip install nltk")
    
    df_result = df.copy()
    
    logger.info(f"Analyzing sentiment for {len(df_result)} records")
    
    # Initialize analyzer once
    analyzer = _get_analyzer()
    
    sentiments = []
    scores = []
    
    for idx, row in df_result.iterrows():
        text = row.get(text_column)
        
        if text is None or str(text).strip() == "":
            sentiments.append("NEUTRAL")
            scores.append(0.0)
        else:
            scores_dict = analyzer.polarity_scores(str(text))
            compound = scores_dict["compound"]
            
            if compound >= 0.5:
                sentiments.append("POSITIVE")
            elif compound <= -0.5:
                sentiments.append("NEGATIVE")
            else:
                sentiments.append("NEUTRAL")
            
            scores.append(compound)
    
    df_result["sentiment"] = sentiments
    df_result["sentiment_score"] = scores
    
    # Summary
    sentiment_counts = df_result["sentiment"].value_counts()
    logger.info("Sentiment distribution:")
    for sentiment, count in sentiment_counts.items():
        percentage = count / len(df_result) * 100
        logger.info(f"  {sentiment}: {count} ({percentage:.1f}%)")
    
    return df_result


def get_sentiment_breakdown(df: pd.DataFrame) -> dict:
    """
    Get summary statistics by sentiment.
    
    Args:
        df: DataFrame with sentiment analysis results
        
    Returns:
        Dictionary with sentiment breakdown statistics
    """
    breakdown = {}
    
    if "sentiment" not in df.columns:
        raise ValueError("DataFrame must contain 'sentiment' column")
    
    for sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
        subset = df[df["sentiment"] == sentiment]
        
        if len(subset) > 0:
            breakdown[sentiment] = {
                "count": len(subset),
                "percentage": round(len(subset) / len(df) * 100, 2),
                "avg_rating": round(subset["rating"].mean(), 2) if "rating" in subset.columns else None,
                "avg_score": round(subset["sentiment_score"].mean(), 4) if "sentiment_score" in subset.columns else None,
            }
        else:
            breakdown[sentiment] = {
                "count": 0,
                "percentage": 0.0,
                "avg_rating": None,
                "avg_score": None,
            }
    
    return breakdown


def generate_sentiment_summary(df: pd.DataFrame) -> str:
    """
    Generate a text summary of sentiment analysis results.
    
    Args:
        df: DataFrame with sentiment analysis results
        
    Returns:
        Formatted string with sentiment summary
    """
    if "sentiment" not in df.columns:
        return "No sentiment analysis results available"
    
    summary_lines = [
        "=" * 60,
        "SENTIMENT ANALYSIS SUMMARY",
        "=" * 60,
        f"Total Reviews Analyzed: {len(df)}",
        "",
    ]
    
    breakdown = get_sentiment_breakdown(df)
    
    for sentiment, stats in breakdown.items():
        summary_lines.append(f"{sentiment}:")
        summary_lines.append(f"  Count: {stats['count']} ({stats['percentage']}%)")
        if stats['avg_rating'] is not None:
            summary_lines.append(f"  Avg Rating: {stats['avg_rating']}")
        if stats['avg_score'] is not None:
            summary_lines.append(f"  Avg Score: {stats['avg_score']}")
        summary_lines.append("")
    
    summary_lines.append("=" * 60)
    
    return "\n".join(summary_lines)


# Example usage
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Perform sentiment analysis on reviews")
    parser.add_argument("input_csv", help="Input CSV file path")
    parser.add_argument("output_csv", help="Output CSV file path with sentiment")
    parser.add_argument("--text-column", default="review_text", help="Column containing review text")
    
    args = parser.parse_args()
    
    print(f"Loading data from: {args.input_csv}")
    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} records\n")
    
    if not nltk_available:
        print("Error: NLTK is required. Install with: pip install nltk")
        sys.exit(1)
    
    print("Performing sentiment analysis...")
    df_with_sentiment = analyze_dataframe(df, text_column=args.text_column)
    
    print(f"\nSaving results to: {args.output_csv}")
    df_with_sentiment.to_csv(args.output_csv, index=False)
    print(f"✓ Saved {len(df_with_sentiment)} records with sentiment")
    
    print(generate_sentiment_summary(df_with_sentiment))
