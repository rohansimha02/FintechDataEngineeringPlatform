{{
  config(
    materialized='view'
  )
}}

with source as (
    select * from {{ source('raw', 'transactions') }}
),

staged as (
    select
        -- Primary key
        time_step,
        
        -- Transaction details
        amount,
        sender_id,
        receiver_id,
        transaction_date,
        transaction_type,
        risk_score,
        
        -- Balance information
        sender_old_balance,
        sender_new_balance,
        receiver_old_balance,
        receiver_new_balance,
        
        -- Fraud indicators
        is_fraud,
        is_flagged_fraud,
        
        -- Derived fields
        transaction_hour,
        transaction_day,
        amount_category,
        high_value_transaction,
        unusual_amount,
        balance_change_ratio,
        
        -- Data quality flags
        case 
            when amount is null then true 
            else false 
        end as is_amount_null,
        
        case 
            when risk_score < 0 or risk_score > 1 then true 
            else false 
        end as is_risk_score_invalid,
        
        case 
            when transaction_date is null then true 
            else false 
        end as is_transaction_date_null
        
    from source
)

select * from staged

-- Data quality tests
{{ config(
    tests=[
        "not_null",
        "unique"
    ]
) }}
