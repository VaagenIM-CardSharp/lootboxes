# Database Setup for Lootboxes Project (MySQL)

This document describes how to design and create a MySQL database for a lootbox system. It includes schema recommendations, example CREATE statements, sample seed data, connection configuration, transactional logic for opening a lootbox, basic maintenance and security guidance.

## 1. Prerequisites
- MySQL server (8.0+ recommended).
- mysql client or a DB GUI (MySQL Workbench, TablePlus).
- Project environment variables for DB connection (host, port, user, password, database).
- (Optional) An ORM or migration tool (Alembic, Flyway, Sequelize, TypeORM, Prisma, etc.).

## 2. High-level model
Typical entities:
- users — players/accounts
- items — possible items (metadata, rarity)
- lootboxes — definitions of box types
- lootbox_items — mapping of items and their drop probabilities per box
- inventories — which items a user owns
- purchases / transactions — purchases and openings (audit)
- logs — activity and errors

## 3. Example schema (SQL)
Run these statements after connecting to MySQL as a user with CREATE DATABASE privileges.

Create database and user (example):
```sql
CREATE DATABASE lootboxes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'loot_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON lootboxes.* TO 'loot_user'@'localhost';
FLUSH PRIVILEGES;
USE lootboxes;
```

Tables:
```sql
-- Users
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Items
CREATE TABLE items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(64),
    rarity ENUM('common','uncommon','rare','epic','legendary') DEFAULT 'common',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lootbox definitions
CREATE TABLE lootboxes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lootbox -> Items mapping with explicit weight/probability
CREATE TABLE lootbox_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    lootbox_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    weight DOUBLE NOT NULL DEFAULT 1, -- relative weight
    probability DOUBLE GENERATED ALWAYS AS (weight) VIRTUAL, -- keep as weight; compute probabilities at runtime
    UNIQUE KEY uq_lootbox_item (lootbox_id, item_id),
    FOREIGN KEY (lootbox_id) REFERENCES lootboxes(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- User inventory
CREATE TABLE inventories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- Transactions / audit
CREATE TABLE transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    lootbox_id BIGINT NULL,
    action ENUM('purchase','open','grant','refund') NOT NULL,
    amount DECIMAL(10,2) NULL,
    currency VARCHAR(10) NULL,
    metadata JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (lootbox_id) REFERENCES lootboxes(id)
);

-- Open results (what the user got)
CREATE TABLE opens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    chance DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- Optional logs
CREATE TABLE logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    level VARCHAR(10),
    message TEXT,
    meta JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Notes:
- Use DOUBLE or BIGINT for weights depending on precision needs. Store weights relative (e.g., 1, 5, 20).
- Probabilities should be computed at runtime by summing weights for a box and dividing each weight by total.
- Use JSON columns for flexible metadata (item skins, stats).

## 4. Seed data examples
```sql
INSERT INTO items (name, type, rarity) VALUES
('Common Hat', 'cosmetic', 'common'),
('Rare Sword', 'weapon', 'rare'),
('Legendary Mount', 'mount', 'legendary');

INSERT INTO lootboxes (key_name, display_name, price) VALUES
('basic_box', 'Basic Box', 0.99),
('premium_box', 'Premium Box', 4.99);

-- Map items to lootboxes with weights
INSERT INTO lootbox_items (lootbox_id, item_id, weight) VALUES
(1, 1, 80),
(1, 2, 15),
(1, 3, 5),
(2, 1, 50),
(2, 2, 35),
(2, 3, 15);
```

## 5. Opening a lootbox (transactional flow)
1. Begin DB transaction.
2. Create a transactions row with action = 'open'.
3. Compute total weight: SELECT SUM(weight) FROM lootbox_items WHERE lootbox_id = ?.
4. Pull items and weights: SELECT item_id, weight FROM lootbox_items WHERE lootbox_id = ?.
5. Use application code (not pure SQL) to pick a random number between 0 and total_weight and select item by cumulative weights. (Alternatively use SQL with RAND() and cumulative sum window functions if MySQL version supports it.)
6. Insert open result into opens and update inventories (INSERT ... ON DUPLICATE KEY UPDATE quantity = quantity + 1).
7. Commit transaction.
8. Log action in transactions and/or logs.

Example inventory insertion:
```sql
INSERT INTO inventories (user_id, item_id, quantity)
VALUES (?, ?, 1)
ON DUPLICATE KEY UPDATE quantity = quantity + 1;
```
(You may need UNIQUE constraint on (user_id, item_id) to make ON DUPLICATE KEY work. Add: UNIQUE KEY uq_user_item (user_id, item_id).)

## 6. Sample SELECT to pick an item in SQL (conceptual)
MySQL 8.0 supports window functions; a SQL-based approach:
```sql
WITH weights AS (
    SELECT item_id, weight,
        SUM(weight) OVER () AS total_weight,
        SUM(weight) OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative
    FROM lootbox_items
    WHERE lootbox_id = ?
)
SELECT item_id FROM weights
WHERE cumulative >= (RAND() * total_weight)
ORDER BY cumulative ASC
LIMIT 1;
```
Test this and adapt to your primary key ordering to ensure deterministic cumulative ordering.

## 7. Connection/configuration
Store credentials in environment variables:
- DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
Example DSN: mysql://loot_user:strong_password@127.0.0.1:3306/lootboxes

If using an ORM, configure pool sizes and timeouts. Use prepared statements and connection pooling.

## 8. Migrations & schema evolution
- Use a migration tool (Flyway, Liquibase, Django/Alembic, Sequelize migration) for schema changes.
- Keep backward-compatible changes when deploying (add columns nullable, backfill, then make non-null).

## 9. Backups, performance, and maintenance
- Regular logical backups: mysqldump or physical backups with Percona XtraBackup.
- Indexes: add indexes on columns used in WHERE/JOIN (lootbox_id, user_id, item_id).
- Partitioning/archiving for very large logs or transaction history.
- Monitor slow queries and use EXPLAIN.
- Consider caching frequently-read data (lootbox definitions, item lists) in memory to reduce DB load.

## 10. Security & integrity
- Use least-privilege DB user for the application.
- Encrypt credentials (avoid committing to source).
- Use TLS for DB connections if remote.
- Validate input on the application side (no SQL concatenation; use prepared statements).
- Consider rate-limiting and anti-farming measures on lootbox openings.

## 11. Testing
- Write unit tests for random selection logic (statistical distribution tests).
- Use a separate test DB or in-memory DB for CI.
- Seed deterministic data for reproducible tests.

## 12. Next steps for README
- Add example environment variables and local dev commands.
- Add sample scripts to create DB and run migrations.
- Document the open transaction flow in application code (with pseudocode or real examples in the project's language/framework).

If you want, I can:
- generate migration files for a specific ORM,
- provide application-side pseudocode for the open-box algorithm,
- add a sample .env template and SQL to create the UNIQUE constraint for inventories.

GitHub Copilot