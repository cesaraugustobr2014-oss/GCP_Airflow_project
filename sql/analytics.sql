-- Analytics queries for customer experience insights

-- 1. Count reviews by source
SELECT 
  ds.source_name,
  COUNT(*) as review_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM customer_experience.fact_reviews fr
JOIN customer_experience.dim_source ds ON fr.source_id = ds.source_id
GROUP BY ds.source_name, ds.source_id
ORDER BY review_count DESC;

-- 2. Sentiment by city
SELECT 
  dl.city,
  fr.sentiment,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY dl.city), 2) as city_percentage
FROM customer_experience.fact_reviews fr
JOIN customer_experience.dim_location dl ON fr.location_id = dl.location_id
GROUP BY dl.city, fr.sentiment
ORDER BY dl.city, count DESC;

-- 3. Overall sentiment distribution
SELECT 
  fr.sentiment,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
  ROUND(AVG(fr.rating), 2) as avg_rating
FROM customer_experience.fact_reviews fr
GROUP BY fr.sentiment
ORDER BY 
  CASE fr.sentiment 
    WHEN 'POSITIVE' THEN 1 
    WHEN 'NEUTRAL' THEN 2 
    WHEN 'NEGATIVE' THEN 3 
  END;

-- 4. Average rating by source
SELECT 
  ds.source_name,
  COUNT(*) as review_count,
  ROUND(AVG(fr.rating), 2) as avg_rating,
  ROUND(STDDEV(fr.rating), 2) as stddev_rating
FROM customer_experience.fact_reviews fr
JOIN customer_experience.dim_source ds ON fr.source_id = ds.source_id
GROUP BY ds.source_name
ORDER BY avg_rating DESC;

-- 5. Rating distribution
SELECT 
  fr.rating,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM customer_experience.fact_reviews fr
GROUP BY fr.rating
ORDER BY fr.rating DESC;

-- 6. Sentiment over time (daily)
SELECT 
  fr.review_date,
  fr.sentiment,
  COUNT(*) as count
FROM customer_experience.fact_reviews fr
GROUP BY fr.review_date, fr.sentiment
ORDER BY fr.review_date DESC;

-- 7. Cities with most negative sentiment
SELECT 
  dl.city,
  dl.state,
  dl.country,
  COUNT(*) as total_reviews,
  SUM(CASE WHEN fr.sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) as negative_reviews,
  ROUND(SUM(CASE WHEN fr.sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as negative_percentage
FROM customer_experience.fact_reviews fr
JOIN customer_experience.dim_location dl ON fr.location_id = dl.location_id
GROUP BY dl.city, dl.state, dl.country
HAVING COUNT(*) >= 10
ORDER BY negative_percentage DESC
LIMIT 20;

-- 8. Correlation between rating and sentiment
SELECT 
  fr.rating,
  fr.sentiment,
  COUNT(*) as count,
  ROUND(AVG(fr.sentiment_score), 4) as avg_sentiment_score
FROM customer_experience.fact_reviews fr
GROUP BY fr.rating, fr.sentiment
ORDER BY fr.rating, fr.sentiment;

-- 9. Monthly trend
SELECT 
  EXTRACT(YEAR FROM fr.review_date) as year,
  EXTRACT(MONTH FROM fr.review_date) as month,
  COUNT(*) as total_reviews,
  ROUND(AVG(fr.rating), 2) as avg_rating,
  ROUND(SUM(CASE WHEN fr.sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as negative_percentage
FROM customer_experience.fact_reviews fr
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- 10. Review count by location
SELECT 
  dl.country,
  dl.state,
  dl.city,
  COUNT(*) as review_count
FROM customer_experience.fact_reviews fr
JOIN customer_experience.dim_location dl ON fr.location_id = dl.location_id
GROUP BY dl.country, dl.state, dl.city
ORDER BY review_count DESC;
