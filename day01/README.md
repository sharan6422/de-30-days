# Day 1: Olist raw load

## Objective

Load all nine raw CSV files, validate their structure, identify primary and foreign keys, and document data-quality issues before building the analytical model.

## 1. Tables and structure

The following are the expected baseline row counts for the standard Olist Brazilian E-Commerce dataset. Verify them against the CSV files you actually downloaded, as published copies may differ slightly.

| Table | Rows | Primary key | Foreign keys | Notes |
|---|---:|---|---|---|
| `customers` | 99,441 | `customer_id` | None | `customer_unique_id` identifies the same real-world customer across orders |
| `orders` | 99,441 | `order_id` | `customer_id` → `customers.customer_id` | One record per order; contains order lifecycle timestamps |
| `order_items` | 112,650 | (`order_id`, `order_item_id`) | `order_id` → `orders.order_id`; `product_id` → `products.product_id`; `seller_id` → `sellers.seller_id` | One record per product line within an order |
| `order_payments` | 103,886 | (`order_id`, `payment_sequential`) | `order_id` → `orders.order_id` | An order can have multiple payment records |
| `order_reviews` | 99,224 | (`review_id`, `order_id`) | `order_id` → `orders.order_id` | Review IDs can repeat across orders; validate the composite grain |
| `products` | 32,951 | `product_id` | `product_category_name` → `product_category_translation.product_category_name` | Contains product dimensions, weight and category |
| `sellers` | 3,095 | `seller_id` | None | Seller identification and location details |
| `geolocation` | 1,000,163 | None | ZIP prefix is a logical lookup to customer/seller ZIP prefixes | Multiple coordinate points can exist per ZIP prefix |
| `product_category_translation` | 71 | `product_category_name` | None | Maps Portuguese category names to English |

> **Validation note:** These are baseline figures, not proof of what was loaded locally. Record the actual row counts from your imported files.

## 2. Data issues found

### A. Key and relationship issues

- `customer_id` is an order-specific customer record identifier. Use `customer_unique_id` when counting distinct real-world customers.
- The dataset contains approximately 96,096 distinct `customer_unique_id` values; verify this with a distinct-count query.
- `review_id` may not be unique on its own. Check duplicates and use (`review_id`, `order_id`) as the candidate composite grain.
- `geolocation` contains multiple coordinate points per ZIP prefix. A direct join can multiply customer, seller, or transaction rows (join fan-out).
- `order_items` has a composite key: (`order_id`, `order_item_id`).
- `order_payments` has a composite key: (`order_id`, `payment_sequential`).

### B. Missing values

- Product category information is missing for some products.
- Review comment titles and messages contain NULL values.
- Several order lifecycle timestamps are missing, particularly for orders that were not successfully delivered.
- Some product categories may not have an English translation.

### C. Data consistency issues

- 14 orders are marked as delivered but have no approval timestamp. **This was reported in the initial profiling; rerun the query to verify it against the raw data.**
- 1 order has no corresponding payment record. **This was reported in the initial profiling; rerun the query to verify it against the raw data.**
- Different order statuses have different expected timestamp patterns. Do not assume every order should have delivery timestamps.
- Product category names are originally in Portuguese and can be mapped to English using the translation table.

### D. Data type issues

- Date and timestamp columns may have been loaded as text; inspect the raw schema and cast them in staging.
- ZIP codes should remain strings to preserve leading zeros.
- Product dimensions and weights should use numeric types.
- Prices, freight values and payment values should use decimal types.
- Review scores should use an integer type.

## 3. Data validation checklist

Before moving to cleaning and transformation, run these checks:

| Validation | What to verify |
|---|---|
| Row counts | Match imported row counts against source CSVs |
| Primary key uniqueness | No duplicate values for single-column keys or composite-key combinations |
| Foreign key integrity | No orphan records in child tables |
| NULL checks | Identify missing values in important columns |
| Timestamp validation | Check invalid, missing and inconsistent dates |
| Duplicate checks | Identify exact duplicates and business-key duplicates |
| Geolocation joins | Ensure joins do not multiply transactional records unexpectedly |
| Payment reconciliation | Compare payment totals with order-level item and freight totals, accounting for business rules |

## 4. SQL validation queries

The following examples use MySQL syntax.

### 4.1 Count distinct real-world customers

```sql
SELECT
    COUNT(*) AS customer_records,
    COUNT(DISTINCT customer_unique_id) AS real_customers
FROM customers;
```

### 4.2 Find repeated review IDs

```sql
SELECT
    review_id,
    COUNT(*) AS occurrences
FROM order_reviews
GROUP BY review_id
HAVING COUNT(*) > 1;
```

Check whether the proposed composite key is unique:

```sql
SELECT
    review_id,
    order_id,
    COUNT(*) AS occurrences
FROM order_reviews
GROUP BY review_id, order_id
HAVING COUNT(*) > 1;
```

### 4.3 Find delivered orders without approval timestamps

```sql
SELECT
    order_id,
    order_status,
    order_approved_at
FROM orders
WHERE order_status = 'delivered'
  AND order_approved_at IS NULL;
```

### 4.4 Find orders without payment records

```sql
SELECT
    o.order_id
FROM orders AS o
LEFT JOIN order_payments AS p
    ON o.order_id = p.order_id
WHERE p.order_id IS NULL;
```

### 4.5 Check duplicate order items

```sql
SELECT
    order_id,
    order_item_id,
    COUNT(*) AS occurrences
FROM order_items
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1;
```

### 4.6 Check ZIP prefixes with multiple geolocation points

```sql
SELECT
    geolocation_zip_code_prefix,
    COUNT(*) AS coordinate_count
FROM geolocation
GROUP BY geolocation_zip_code_prefix
HAVING COUNT(*) > 1
ORDER BY coordinate_count DESC;
```

## 5. Day 1 deliverables

- [ ] Downloaded all 9 Olist CSV files.
- [ ] Created the database and 9 raw tables.
- [ ] Imported all CSV files successfully.
- [ ] Verified row counts against source files.
- [ ] Identified primary and foreign keys.
- [ ] Documented table grain and relationships.
- [ ] Checked NULL values and duplicates.
- [ ] Identified referential-integrity issues.
- [ ] Identified timestamp and datatype issues.
- [ ] Documented geolocation join fan-out risk.

## 6. Day 1 conclusion

The Olist dataset contains approximately 100,000 orders across nine related tables. Although the dataset has a relational structure, it presents data-quality challenges involving customer identity, review identifiers, missing timestamps, incomplete payment records and geographic join cardinality.

The raw data should remain unchanged. Data type conversions, missing-value handling, deduplication and relationship validation should happen in a separate staging layer.

**Day 1 outcome:** Raw data loaded, database structure documented, and initial data-quality issues identified.

## Important modelling note

Do not blindly delete repeated review IDs or geolocation records. First establish their business meaning and determine whether they are genuine duplicates. Preserve the raw data so that all cleaning decisions remain reproducible.

## Next step

**Day 2: Data cleaning and staging transformations** — profile each column, standardize data types, investigate anomalies, and create cleaned staging tables while preserving the raw source tables.

## How to run
docker run -d --name pg -e POSTGRES_PASSWORD=pg -p 5433:5432 postgres:16
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install pandas sqlalchemy "psycopg[binary]"
python day01\load_olist.py

## Problems I hit and how I solved them
- Port 5432 already taken by a local Windows Postgres → mapped Docker to 5433
- Loader failed on order_items: Postgres allows max 65,535 bind params per
  statement; 7 cols × 10,000 rows = 70,000 → chunk size = 65,535 // n_cols
- DBeaver: JVM timezone "Asia/Calcutta" rejected by Postgres → set Asia/Kolkata
- My information_schema query returned a system table: AND binds tighter than OR