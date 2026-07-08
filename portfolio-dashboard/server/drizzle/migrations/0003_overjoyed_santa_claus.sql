-- stock_meta のシードデータ（INSERT OR IGNORE で冪等）
INSERT OR IGNORE INTO stock_meta (code, color, market, sort_order)
VALUES
  ('7974.T', '#E53935', '東証プライム', 0),
  ('2432.T', '#1565C0', '東証プライム', 1),
  ('NVDA',   '#76B900', 'NASDAQ',       2);