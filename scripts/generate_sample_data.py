#!/usr/bin/env python3
"""
Generate synthetic customer reviews dataset.

This script creates a realistic reviews dataset with intentional data quality issues
for demonstration purposes in a Customer Experience Data Pipeline project.

Data Quality Issues Included:
- Duplicate records (1%)
- Null text (0.5%)
- Invalid ratings (out of 1-5 range, 1%)
- Missing city (0.5%)
- Invalid dates (0.5%)
- Extra whitespace in text (2%)
- Inconsistent casing in source (1%)
- Incomplete records (0.5%)

Usage:
    python scripts/generate_sample_data.py [--output-path PATH] [--num-records N]
"""

import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Set seed for reproducibility
random.seed(42)

# Configuration
BASE_DIR = Path(__file__).parent.parent
DEFAULT_OUTPUT_PATH = BASE_DIR / "data" / "sample" / "reviews.csv"
DEFAULT_NUM_RECORDS = 10000

# Valid sources
SOURCES = [
    "google_reviews",
    "tripadvisor",
    "yelp",
    "email",
    "social_media"
]

# Valid cities (Brazilian cities)
CITIES = [
    ("São Paulo", "SP", "BR"),
    ("Rio de Janeiro", "RJ", "BR"),
    ("Belo Horizonte", "MG", "BR"),
    ("Salvador", "BA", "BR"),
    ("Fortaleza", "CE", "BR"),
    ("Brasília", "DF", "BR"),
    ("Curitiba", "PR", "BR"),
    ("Manaus", "AM", "BR"),
    ("Recife", "PE", "BR"),
    ("Porto Alegre", "RS", "BR"),
    ("Belém", "PA", "BR"),
    ("Goiânia", "GO", "BR"),
    ("Guarulhos", "SP", "BR"),
    ("Campinas", "SP", "BR"),
    ("São Luís", "MA", "BR"),
]

# Review text templates (Portuguese)
POSITIVE_TEMPLATES = [
    "O atendimento foi excelente e a experiência foi incrível.",
    "Recebi um ótimo serviço, vou recomendar para amigos.",
    "A qualidade foi superior às expectativas, muito satisfeito.",
    "Equipe muito profissional e atenciosa.",
    "Produto de altíssima qualidade, superou minhas expectativas.",
    "Muito obrigado pela atenção, tudo perfeito!",
    "Excelente experiência, certamente retornarei.",
    "A melhor experiência que já tive com este tipo de serviço.",
]

NEUTRAL_TEMPLATES = [
    "O serviço foi ok, nada de extraordinário.",
    "Atendimento razoável, como o esperado.",
    "A experiência foi satisfatória, mas não excepcional.",
    "O processo foi normal, sem grandes problemas.",
    "Bom, mas poderia ser melhor em alguns aspectos.",
    "Recebi o que foi prometido, nada a reclamar.",
    "O serviço atingiu o padrão médio.",
    "Não tive problemas, mas não fiquei impressionado.",
]

NEGATIVE_TEMPLATES = [
    "O atendimento demorou muito e tive problemas com a reserva.",
    "A qualidade do produto foi ruim, não valia o preço pago.",
    "Funcionário foi descuidado e o serviço foi péssimo.",
    "Tive uma experiência negativa, vou procurar outro fornecedor.",
    "O problema não foi resolvido e o suporte foi ineficiente.",
    "Expectativa não atendida, produto danificado na entrega.",
    "Pior experiência que já tive, recomendo evitar.",
    "Demorei dias para receber resposta e nada Resolveu.",
]

RATINGS_BY_SENTIMENT = {
    "positive": [4, 5],
    "neutral": [3],
    "negative": [1, 2],
}


def generate_review_id(index: int) -> str:
    """Generate a unique review ID."""
    return f"REV{index:06d}"


def generate_customer_id(index: int) -> str:
    """Generate a customer ID."""
    return f"CUS{random.randint(1, 5000):03d}"


def generate_rating(sentiment: str) -> int:
    """Generate a rating based on sentiment."""
    return random.choice(RATINGS_BY_SENTIMENT[sentiment])


def generate_review_text(sentiment: str) -> str:
    """Generate review text based on sentiment."""
    if sentiment == "positive":
        return random.choice(POSITIVE_TEMPLATES)
    elif sentiment == "neutral":
        return random.choice(NEUTRAL_TEMPLATES)
    else:
        return random.choice(NEGATIVE_TEMPLATES)


def generate_review_date() -> str:
    """Generate a random review date within the last 90 days."""
    base_date = datetime.now()
    random_days = random.randint(0, 90)
    review_date = base_date - timedelta(days=random_days)
    return review_date.strftime("%Y-%m-%d")


def generate_ingestion_timestamp() -> str:
    """Generate ingestion timestamp (fixed for reproducibility)."""
    # Use fixed timestamp for reproducibility in tests
    return "2026-09-12T21:00:00"


def apply_data_quality_issues(review: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Apply intentional data quality issues to a review."""
    
    # Check if this record should have issues (5% chance)
    if random.random() > 0.05:
        return review
    
    issue_type = random.choice([
        "duplicate",
        "null_text",
        "invalid_rating",
        "missing_city",
        "invalid_date",
        "extra_whitespace",
        "inconsistent_source_case",
        "incomplete",
    ])
    
    if issue_type == "duplicate":
        # Make it identical to previous record (will be handled during deduplication)
        pass
    
    elif issue_type == "null_text":
        review["review_text"] = None
    
    elif issue_type == "invalid_rating":
        # Out of range rating
        review["rating"] = random.choice([0, 6, -1, 10])
    
    elif issue_type == "missing_city":
        review["city"] = None
    
    elif issue_type == "invalid_date":
        review["review_date"] = "9999-99-99"
    
    elif issue_type == "extra_whitespace":
        review["review_text"] = "   " + review["review_text"] + "   "
        review["city"] = "  " + review["city"] + "  " if review.get("city") else None
    
    elif issue_type == "inconsistent_source_case":
        review["source"] = random.choice([
            review["source"].upper(),
            review["source"].lower(),
            review["source"].title(),
            review["source"].swapcase(),
        ])
    
    elif issue_type == "incomplete":
        # Remove some fields
        review.pop("customer_id", None)
        review["rating"] = None
    
    return review


def generate_reviews(num_records: int = DEFAULT_NUM_RECORDS) -> List[Dict[str, Any]]:
    """Generate a list of reviews."""
    reviews = []
    
    for i in range(1, num_records + 1):
        # Determine sentiment distribution (60% positive, 20% neutral, 20% negative)
        rand_val = random.random()
        if rand_val < 0.6:
            sentiment = "positive"
        elif rand_val < 0.8:
            sentiment = "neutral"
        else:
            sentiment = "negative"
        
        # Generate city (may be None)
        if random.random() < 0.005:  # 0.5% missing city
            city, state, country = None, None, None
        else:
            city, state, country = random.choice(CITIES)
        
        review = {
            "review_id": generate_review_id(i),
            "source": random.choice(SOURCES),
            "customer_id": generate_customer_id(i),
            "city": city,
            "state": state,
            "country": country,
            "rating": generate_rating(sentiment),
            "review_text": generate_review_text(sentiment),
            "review_date": generate_review_date(),
            "ingestion_timestamp": generate_ingestion_timestamp(),
        }
        
        # Apply data quality issues
        review = apply_data_quality_issues(review, i)
        
        reviews.append(review)
    
    return reviews


def write_reviews_to_csv(reviews: List[Dict[str, Any]], output_path: Path) -> None:
    """Write reviews to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "review_id",
        "source",
        "customer_id",
        "city",
        "state",
        "country",
        "rating",
        "review_text",
        "review_date",
        "ingestion_timestamp",
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reviews)
    
    print(f"✓ Generated {len(reviews)} reviews")
    print(f"✓ Output saved to: {output_path}")


def print_statistics(reviews: List[Dict[str, Any]]) -> None:
    """Print statistics about the generated dataset."""
    total = len(reviews)
    
    # Count by source
    sources = {}
    for r in reviews:
        src = r.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    
    # Count by rating
    ratings = {}
    for r in reviews:
        rating = r.get("rating")
        if rating is not None:
            ratings[rating] = ratings.get(rating, 0) + 1
    
    # Count issues
    null_texts = sum(1 for r in reviews if r.get("review_text") is None)
    invalid_ratings = sum(1 for r in reviews if r.get("rating") not in [1, 2, 3, 4, 5])
    missing_cities = sum(1 for r in reviews if r.get("city") is None)
    
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    print(f"Total Records: {total}")
    print(f"\nRecords by Source:")
    for src, count in sorted(sources.items()):
        print(f"  {src}: {count} ({count/total*100:.1f}%)")
    print(f"\nRecords by Rating:")
    for rating in sorted(ratings.keys()):
        print(f"  {rating}: {ratings[rating]} ({ratings[rating]/total*100:.1f}%)")
    print(f"\nData Quality Issues:")
    print(f"  Null text: {null_texts} ({null_texts/total*100:.2f}%)")
    print(f"  Invalid ratings: {invalid_ratings} ({invalid_ratings/total*100:.2f}%)")
    print(f"  Missing cities: {missing_cities} ({missing_cities/total*100:.2f}%)")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic customer reviews dataset"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output path for CSV file (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--num-records",
        type=int,
        default=DEFAULT_NUM_RECORDS,
        help=f"Number of records to generate (default: {DEFAULT_NUM_RECORDS})",
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output_path)
    num_records = args.num_records
    
    print(f"Generating {num_records} synthetic customer reviews...")
    print(f"Output: {output_path}")
    print()
    
    reviews = generate_reviews(num_records)
    write_reviews_to_csv(reviews, output_path)
    print_statistics(reviews)
    
    return 0


if __name__ == "__main__":
    exit(main())
