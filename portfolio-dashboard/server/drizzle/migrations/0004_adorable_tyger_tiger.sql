CREATE TABLE IF NOT EXISTS `wp_posts` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`month` text NOT NULL,
	`url` text NOT NULL,
	`title` text,
	`created_at` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `uq_wp_posts_month` ON `wp_posts` (`month`);--> statement-breakpoint
-- 本番 DB に重複行が既にある場合でも UNIQUE INDEX の作成が失敗しないよう、
-- date, code が重複する行のうち最小 id 以外を削除しておく
DELETE FROM dividends WHERE id NOT IN (SELECT MIN(id) FROM dividends GROUP BY date, code);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `uq_dividends_date_code` ON `dividends` (`date`,`code`);
