with source as (
    -- Pull everything from the raw table
    select * from {{ source('raw', 'raw_books') }}

),
cleaned as (
    select
        id,
        upc,
        trim(title)     as title,
        -- Fix bad categories with professional naming
        case
            when trim(category) in ('Add a comment', 'Default', '', 'Unknown', 'Uncategorized')
                then 'General Collection'
            else trim(category)
        end             as category,
        rating,
        rating_word,
        round(price, 2)          as price,
        round(price_excl_tax, 2) as price_excl_tax,
        round(price_incl_tax, 2) as price_incl_tax,
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
        num_reviews,
        description,
        url,
        scraped_at,
        loaded_at

    from source

)

select * from cleaned