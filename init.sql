-- Initialize database with default data

-- Create default roles
INSERT INTO user_roles (name, description) VALUES 
('guest', 'Гость - ограниченный доступ'),
('reader', 'Читатель - полный доступ к чтению'),
('librarian', 'Библиотекарь - управление контентом'),
('admin', 'Администратор - полный доступ к системе')
ON CONFLICT (name) DO NOTHING;

-- Create default admin user
INSERT INTO users (username, email, full_name, hashed_password, role_id, is_active, created_at, updated_at)
SELECT 
    'admin',
    'admin@library.local',
    'Системный администратор',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OWe5pVj5tj.2J7Qo2i8U9yQqLQpVqVqVqW', -- password: admin123
    id,
    true,
    NOW(),
    NOW()
FROM user_roles 
WHERE name = 'admin'
ON CONFLICT (username) DO NOTHING;

-- Create default categories
INSERT INTO categories (name, description, created_at, updated_at) VALUES 
('Художественная литература', 'Романы, повести, рассказы', NOW(), NOW()),
('Научная литература', 'Научные работы, исследования', NOW(), NOW()),
('Учебная литература', 'Учебники, пособия, справочники', NOW(), NOW()),
('Детская литература', 'Книги для детей и подростков', NOW(), NOW()),
('Бизнес и карьера', 'Книги по бизнесу, экономике, саморазвитию', NOW(), NOW()),
('Психология', 'Книги по психологии и самопознанию', NOW(), NOW()),
('История', 'Исторические книги и биографии', NOW(), NOW()),
('Философия', 'Философские трактаты и исследования', NOW(), NOW()),
('Религия', 'Религиозные тексты и духовная литература', NOW(), NOW()),
('Искусство', 'Книги об искусстве, дизайне, архитектуре', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Create default authors
INSERT INTO authors (first_name, last_name, bio, birth_date, created_at, updated_at) VALUES 
('Лев', 'Толстой', 'Великий русский писатель, мыслитель и общественный деятель', '1828-09-09', NOW(), NOW()),
('Фёдор', 'Достоевский', 'Русский писатель, мыслитель, философ и публицист', '1821-11-11', NOW(), NOW()),
('Антон', 'Чехов', 'Русский писатель и драматург', '1860-01-29', NOW(), NOW()),
('Александр', 'Пушкин', 'Русский поэт, драматург и прозаик', '1799-06-06', NOW(), NOW()),
('Михаил', 'Лермонтов', 'Русский поэт, прозаик, драматург', '1814-10-15', NOW(), NOW()),
('Николай', 'Гоголь', 'Русский прозаик, драматург, поэт', '1809-04-01', NOW(), NOW()),
('Иван', 'Тургенев', 'Русский писатель-реалист, поэт, публицист', '1818-11-09', NOW(), NOW()),
('Сергей', 'Есенин', 'Русский поэт, представитель крестьянской поэзии', '1895-10-03', NOW(), NOW()),
('Владимир', 'Маяковский', 'Русский советский поэт', '1893-07-19', NOW(), NOW()),
('Анна', 'Ахматова', 'Русская поэтесса, переводчица и литературовед', '1889-06-23', NOW(), NOW())
ON CONFLICT (first_name, last_name) DO NOTHING;

-- Create sample books
INSERT INTO books (title, subtitle, isbn, description, publication_year, language, pages, file_path, file_size, file_format, is_active, created_at, updated_at) VALUES 
('Война и мир', 'Роман-эпопея', '978-5-17-070490-3', 'Великий роман о жизни российского общества во время наполеоновских войн', 1869, 'ru', 1225, '/books/war_and_peace.pdf', 15728640, 'PDF', true, NOW(), NOW()),
('Преступление и наказание', 'Роман', '978-5-17-080491-4', 'Психологический роман о преступлении и раскаянии', 1866, 'ru', 671, '/books/crime_and_punishment.pdf', 8388608, 'PDF', true, NOW(), NOW()),
('Анна Каренина', 'Роман', '978-5-17-090492-5', 'Роман о трагической любви и социальных проблемах', 1877, 'ru', 864, '/books/anna_karenina.pdf', 10485760, 'PDF', true, NOW(), NOW()),
('Евгений Онегин', 'Роман в стихах', '978-5-17-100493-6', 'Классический роман в стихах о любви и дружбе', 1833, 'ru', 224, '/books/evgeny_onegin.pdf', 3145728, 'PDF', true, NOW(), NOW()),
('Мастер и Маргарита', 'Роман', '978-5-17-110494-7', 'Мистический роман о визите дьявола в советскую Москву', 1967, 'ru', 448, '/books/master_and_margarita.pdf', 5242880, 'PDF', true, NOW(), NOW()),
('Чайка', 'Пьеса', '978-5-17-120495-8', 'Классическая пьеса о любви и искусстве', 1896, 'ru', 96, '/books/the_seagull.pdf', 1048576, 'PDF', true, NOW(), NOW())
ON CONFLICT (isbn) DO NOTHING;

-- Link books with authors
INSERT INTO book_authors (book_id, author_id) VALUES 
(1, 1), -- Война и мир - Лев Толстой
(2, 2), -- Преступление и наказание - Фёдор Достоевский
(3, 1), -- Анна Каренина - Лев Толстой
(4, 4), -- Евгений Онегин - Александр Пушкин
(5, 10), -- Мастер и Маргарита - Михаил Булгаков (need to add)
(6, 3)  -- Чайка - Антон Чехов
ON CONFLICT (book_id, author_id) DO NOTHING;

-- Link books with categories
INSERT INTO book_categories (book_id, category_id) VALUES 
(1, 1), -- Война и мир - Художественная литература
(2, 1), -- Преступление и наказание - Художественная литература
(3, 1), -- Анна Каренина - Художественная литература
(4, 1), -- Евгений Онегин - Художественная литература
(5, 1), -- Мастер и Маргарита - Художественная литература
(6, 1)  -- Чайка - Художественная литература
ON CONFLICT (book_id, category_id) DO NOTHING;

-- Create sample reviews
INSERT INTO reviews (book_id, user_id, rating, text, created_at, updated_at) VALUES 
(1, 1, 5, 'Величайшее произведение русской литературы. Обязательно к прочтению!', NOW(), NOW()),
(2, 1, 5, 'Глубокий психологический роман, заставляет задуматься о вечных вопросах', NOW(), NOW()),
(3, 1, 4, 'Трагическая история любви, прекрасно написано', NOW(), NOW()),
(4, 1, 5, 'Гениальный роман в стихах, каждое слово на своем месте', NOW(), NOW()),
(5, 1, 5, 'Мистический шедевр Булгакова, перечитываю постоянно', NOW(), NOW())
ON CONFLICT (book_id, user_id) DO NOTHING;
