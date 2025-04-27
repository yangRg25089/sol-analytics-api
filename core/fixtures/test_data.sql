-- Users
INSERT INTO api_user (id, password, username, email, google_id, solana_address, is_active, created_at, updated_at, is_superuser, is_staff, first_name, last_name, date_joined, last_login) VALUES
(1, 'pbkdf2_sha256$260000$test_password', 'admin', 'admin@example.com', 'google_123456', 'HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH', 1, '2024-03-22 00:00:00', '2024-03-22 00:00:00', 1, 1, '', '', '2024-03-22 00:00:00', NULL),
(2, 'pbkdf2_sha256$260000$test_password', 'user1', 'user1@example.com', 'google_234567', '5tzFkiKscXHK5ZXCGbXZxgP3r5WyLHyfXc8CTqpmjH1E', 1, '2024-03-22 00:00:00', '2024-03-22 00:00:00', 0, 0, '', '', '2024-03-22 00:00:00', NULL),
(3, 'pbkdf2_sha256$260000$test_password', 'user2', 'user2@example.com', 'google_345678', '7XxuQBJvD5KbYXJUemJ5UQRUkHgYZaL1U5kh1qY3Yp2F', 1, '2024-03-22 00:00:00', '2024-03-22 00:00:00', 0, 0, '', '', '2024-03-22 00:00:00', NULL);

-- Tokens
INSERT INTO api_token (id, name, symbol, total_supply, owner_id, created_at, updated_at) VALUES
(1, 'Test Token 1', 'TT1', 1000000.000000000, 1, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(2, 'Test Token 2', 'TT2', 2000000.000000000, 1, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(3, 'Test Token 3', 'TT3', 3000000.000000000, 2, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(4, 'Test Token 4', 'TT4', 4000000.000000000, 2, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(5, 'Test Token 5', 'TT5', 5000000.000000000, 3, '2024-03-22 00:00:00', '2024-03-22 00:00:00');

-- Transactions
INSERT INTO api_transaction (id, token_id, from_address, to_address, amount, timestamp, created_at, updated_at) VALUES
(1, 1, 'HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH', '5tzFkiKscXHK5ZXCGbXZxgP3r5WyLHyfXc8CTqpmjH1E', 100.000000000, '2024-03-22 00:00:00', '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(2, 1, '5tzFkiKscXHK5ZXCGbXZxgP3r5WyLHyfXc8CTqpmjH1E', '7XxuQBJvD5KbYXJUemJ5UQRUkHgYZaL1U5kh1qY3Yp2F', 50.000000000, '2024-03-22 00:01:00', '2024-03-22 00:01:00', '2024-03-22 00:01:00'),
(3, 2, 'HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH', '5tzFkiKscXHK5ZXCGbXZxgP3r5WyLHyfXc8CTqpmjH1E', 200.000000000, '2024-03-22 00:02:00', '2024-03-22 00:02:00', '2024-03-22 00:02:00'),
(4, 3, '5tzFkiKscXHK5ZXCGbXZxgP3r5WyLHyfXc8CTqpmjH1E', 'HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH', 300.000000000, '2024-03-22 00:03:00', '2024-03-22 00:03:00', '2024-03-22 00:03:00'),
(5, 4, '7XxuQBJvD5KbYXJUemJ5UQRUkHgYZaL1U5kh1qY3Yp2F', '5tzFkiKscXHK5ZXCGbXZxgP3r5WyLHyfXc8CTqpmjH1E', 400.000000000, '2024-03-22 00:04:00', '2024-03-22 00:04:00', '2024-03-22 00:04:00');

-- Favorites
INSERT INTO api_favorite (id, user_id, token_id, created_at, updated_at) VALUES
(1, 1, 2, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(2, 1, 3, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(3, 2, 1, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(4, 2, 4, '2024-03-22 00:00:00', '2024-03-22 00:00:00'),
(5, 3, 5, '2024-03-22 00:00:00', '2024-03-22 00:00:00');
