CREATE TABLE IF NOT EXISTS `ai_comments` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`date` text NOT NULL,
	`code` text DEFAULT '' NOT NULL,
	`kind` text NOT NULL,
	`content` text NOT NULL,
	`created_at` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `uq_ai_comments_date_code_kind` ON `ai_comments` (`date`,`code`,`kind`);--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `stock_meta` (
	`code` text PRIMARY KEY NOT NULL,
	`color` text NOT NULL,
	`market` text NOT NULL,
	`sort_order` integer DEFAULT 0 NOT NULL
);
