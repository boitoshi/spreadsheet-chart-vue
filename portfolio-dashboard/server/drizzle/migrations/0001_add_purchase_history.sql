CREATE TABLE `purchase_history` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`code` text NOT NULL,
	`seq` integer NOT NULL,
	`shares` real NOT NULL,
	`price` real NOT NULL,
	`price_foreign` real,
	`exchange_rate` real,
	`purchased_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `uq_purchase_history_code_seq` ON `purchase_history` (`code`,`seq`);
