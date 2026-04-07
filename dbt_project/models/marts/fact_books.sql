with books as (
    select * from {{ ref('stg_books') }}
)
select
    id              as book_id,
    upc,
    title,
    category,
    rating,
    rating_word,
    price,
    price_excl_tax,
    price_incl_tax,
    in_stock,
    stock_count,
    num_reviews,
    description,
    url,
    scraped_at,
    loaded_at

from books
