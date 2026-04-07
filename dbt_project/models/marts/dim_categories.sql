
with stg as (

    select * from {{ ref('stg_books') }}
),

category_stats as (
    select
        category,
        count(*)                        as total_books,
        count(case when in_stock = true then 1 end) as books_in_stock,
        count(case when in_stock = false then 1 end) as books_out_of_stock,
        round(min(price), 2)            as min_price,
        round(max(price), 2)            as max_price,
        round(avg(price), 2)            as avg_price,
        round(avg(rating), 2)           as avg_rating,
        max(scraped_at)                 as last_scraped_at

    from stg
    group by category

)

select * from category_stats
