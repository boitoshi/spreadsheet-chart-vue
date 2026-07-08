CREATE TABLE IF NOT EXISTS `benchmark_data` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`date` text NOT NULL,
	`portfolio` real NOT NULL,
	`nikkei225` real,
	`sp500` real
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `uq_benchmark_data_date` ON `benchmark_data` (`date`);--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `dividends` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`date` text NOT NULL,
	`code` text NOT NULL,
	`name` text NOT NULL,
	`dividend_foreign` real,
	`shares` real NOT NULL,
	`total_foreign` real,
	`currency` text DEFAULT 'JPY' NOT NULL,
	`exchange_rate` real,
	`total_jpy` real NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `exchange_rates` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`date` text NOT NULL,
	`pair` text NOT NULL,
	`rate` real NOT NULL,
	`prev_rate` real,
	`change_rate` real,
	`high` real,
	`low` real,
	`updated_at` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `uq_exchange_rates_date_pair` ON `exchange_rates` (`date`,`pair`);--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `holdings` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`code` text NOT NULL,
	`name` text NOT NULL,
	`acquired_date` text,
	`acquired_price_jpy` real NOT NULL,
	`acquired_price_foreign` real,
	`acquired_exchange_rate` real,
	`shares` real NOT NULL,
	`currency` text DEFAULT 'JPY' NOT NULL,
	`is_foreign` integer DEFAULT false NOT NULL,
	`memo` text,
	`updated_at` text
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_holdings_code` ON `holdings` (`code`);--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `monthly_pnl` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`date` text NOT NULL,
	`code` text NOT NULL,
	`name` text NOT NULL,
	`acquired_price` real NOT NULL,
	`current_price` real NOT NULL,
	`shares` real NOT NULL,
	`cost` real NOT NULL,
	`value` real NOT NULL,
	`profit` real NOT NULL,
	`profit_rate` real NOT NULL,
	`currency` text DEFAULT 'JPY' NOT NULL,
	`acquired_price_foreign` real,
	`current_price_foreign` real,
	`acquired_exchange_rate` real,
	`current_exchange_rate` real,
	`updated_at` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `uq_monthly_pnl_date_code` ON `monthly_pnl` (`date`,`code`);--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_monthly_pnl_date` ON `monthly_pnl` (`date`);--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `monthly_prices` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`date` text NOT NULL,
	`code` text NOT NULL,
	`price_jpy` real NOT NULL,
	`high` real,
	`low` real,
	`average` real,
	`change_rate` real,
	`avg_volume` real,
	`created_at` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `uq_monthly_prices_date_code` ON `monthly_prices` (`date`,`code`);
