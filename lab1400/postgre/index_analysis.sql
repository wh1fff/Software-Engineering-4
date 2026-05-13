EXPLAIN ANALYZE 
SELECT * FROM order_items WHERE order_id = 1;
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
EXPLAIN ANALYZE 
SELECT * FROM order_items WHERE order_id = 1;