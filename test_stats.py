import sqlite3

conn = sqlite3.connect('supermarket.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
q = """
SELECT u.full_name as cashier, p.name as product,
date(s.sale_date) as period,
SUM(si.qty) as total_qty,
SUM(si.qty * si.unit_price) as total_amount
FROM sales s
JOIN sale_items si ON s.id = si.sale_id
JOIN products p ON si.product_id = p.id
JOIN users u ON s.user_id = u.id
WHERE date(s.sale_date) >= '2026-03-01' AND date(s.sale_date) <= '2026-03-04'
GROUP BY u.id, p.id, period
ORDER BY u.full_name, period, product
"""
for row in cur.execute(q):
    print(dict(row))
conn.close()
