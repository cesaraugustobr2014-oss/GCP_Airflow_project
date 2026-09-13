-- Data quality checks for customer reviews

-- 1. Check for duplicate review IDs
SELECT 
  'duplicates_review_id' as check_name,
  COUNT(*) - COUNT(DISTINCT review_id) as violation_count,
  COUNT(*) as total_records,
  CASE 
    WHEN COUNT(*) - COUNT(DISTINCT review_id) > 0 THEN 'FAIL'
    ELSE 'PASS'
  END as status
FROM customer_experience.fact_reviews;

-- 2. Check for null review_id
SELECT 
  'null_review_id' as check_name,
  COUNT(*) as violation_count,
  CASE 
    WHEN COUNT(*) > 0 THEN 'FAIL'
    ELSE 'PASS'
  END as status
FROM customer_experience.fact_reviews
WHERE review_id IS NULL;

-- 3. Check for invalid ratings (outside 1-5 range)
SELECT 
  'invalid_rating_range' as check_name,
  COUNT(*) as violation_count,
  CASE 
    WHEN COUNT(*) > 0 THEN 'FAIL'
    ELSE 'PASS'
  END as status
FROM customer_experience.fact_reviews
WHERE rating < 1 OR rating > 5 OR rating IS NULL;

-- 4. Check for empty review text
SELECT 
  'empty_review_text' as check_name,
  COUNT(*) as violation_count,
  CASE 
    WHEN COUNT(*) > 0 THEN 'FAIL'
    ELSE 'PASS'
  END as status
FROM customer_experience.fact_reviews
WHERE review_text IS NULL OR TRIM(review_text) = '';

-- 5. Check for invalid sentiment values
SELECT 
  'invalid_sentiment' as check_name,
  COUNT(*) as violation_count,
  CASE 
    WHEN COUNT(*) > 0 THEN 'FAIL'
    ELSE 'PASS'
  END as status
FROM customer_experience.fact_reviews
WHERE sentiment NOT IN ('POSITIVE', 'NEUTRAL', 'NEGATIVE');

-- 6. Check sentiment score range
SELECT 
  'invalid_sentiment_score' as check_name,
  COUNT(*) as violation_count,
  CASE 
    WHEN COUNT(*) > 0 THEN 'FAIL'
    ELSE 'PASS'
  END as status
FROM customer_experience.fact_reviews
WHERE sentiment_score < -1.0 OR sentiment_score > 1.0;

-- 7. Check for invalid date formats
SELECT 
  'invalid_review_date' as check_name,
  COUNT(*) as violation_count,
  CASE 
    WHEN COUNT(*) > 0 THEN 'FAIL'
    ELSE 'PASS'
  END as status
FROM customer_experience.fact_reviews
WHERE review_date IS NULL;

-- Summary statistics
SELECT 
  'summary' as check_type,
  COUNT(*) as total_reviews,
  COUNT(DISTINCT review_id) as unique_reviews,
  COUNT(DISTINCT source_id) as unique_sources,
  COUNT(DISTINCT location_id) as unique_locations,
  COUNT(DISTINCT DATE(review_date)) as review_days
FROM customer_experience.fact_reviews;
