
with source as (
    -- Pull everything from the raw table
    select * from {{ source('raw', 'raw_books') }}

),
cleaned as (

    select
        id,
        upc,
        trim(title)     as title,
        -- Fix bad categories
        -- Some books have 'Add a comment' or 'Default' as category
        case
            when trim(category) in ('Add a comment', 'Default', '')
                then 'Unknown'
            else trim(category)
        end             as category,

        -- Ratings
        rating,
        rating_word,

        -- Prices — round to 2 decimal places for consistency
        round(price, 2)          as price,
        round(price_excl_tax, 2) as price_excl_tax,
        round(price_incl_tax, 2) as price_incl_tax,

        -- Stock
        in_stock,

        -- Extract just the number from "In stock (22 available)"
        -- If it says "In stock" with no number, default to 0
        case
            when availability ilike '%(%'
                then try_to_number(
                    regexp_substr(availability, '\\d+')
                )
            when availability ilike 'in stock'
                then 0
            else null
        end             as stock_count,

        -- Reviews
        num_reviews,

        -- Description
        description,

        -- URL
        url,

        -- Timestamps
        scraped_at,
        loaded_at

    from source

)

select * from cleaned
