{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['date'], 'type': 'btree'},
      {'columns': ['transaction_type'], 'type': 'btree'}
    ]
  )
}}

with daily_stats as (
    select
        date(transaction_date) as date,
        transaction_type,
        count(*) as transaction_count,
        sum(amount) as total_volume,
        avg(amount) as avg_amount,
        avg(risk_score) as avg_risk_score,
        count(case when risk_score > 0.7 then 1 end) as high_risk_count,
        count(case when risk_score > 0.9 then 1 end) as critical_risk_count,
        count(distinct sender_id) as unique_senders,
        count(distinct receiver_id) as unique_receivers
        
    from {{ ref('stg_transactions') }}
    
    group by 1, 2
),

daily_aggregate as (
    select
        date,
        'ALL' as transaction_type,
        sum(transaction_count) as transaction_count,
        sum(total_volume) as total_volume,
        sum(total_volume) / sum(transaction_count) as avg_amount,
        sum(avg_risk_score * transaction_count) / sum(transaction_count) as avg_risk_score,
        sum(high_risk_count) as high_risk_count,
        sum(critical_risk_count) as critical_risk_count,
        max(unique_senders) as unique_senders,
        max(unique_receivers) as unique_receivers
        
    from daily_stats
    
    group by 1
)

select * from daily_stats
union all
select * from daily_aggregate

order by date, transaction_type
