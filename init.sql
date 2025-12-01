
-- Создаем хотя бы одну категорию для проверки
INSERT INTO categories (name, description, is_active, created_at) 
VALUES 
('Художественная литература', 'Романы, повести, рассказы', true, NOW())
ON CONFLICT (name) DO NOTHING;

-- Создаем одного автора для проверки
INSERT INTO authors (first_name, last_name, bio, created_at) 
VALUES 
('Лев', 'Толстой', 'Великий русский писатель', NOW())
ON CONFLICT (first_name, last_name) DO NOTHING;

-- Создаем одну книгу для проверки
INSERT INTO books (
    title, subtitle, isbn, description, publication_year, 
    language, pages, file_format, cover_url, rating, 
    download_count, view_count, is_active, is_featured, created_at
) VALUES 
(
    'Война и мир',
    'Роман-эпопея',
    '978-5-17-070490-3',
    'Великий роман о жизни российского общества во время наполеоновских войн.',
    1869,
    'ru',
    1225,
    'PDF',
    '/covers/war_and_peace.jpg',
    4.8,
    1500,
    4500,
    true,
    true,
    NOW()
)
ON CONFLICT (isbn) DO NOTHING;

-- Связываем книгу с автором
INSERT INTO book_authors (book_id, author_id) 
SELECT b.id, a.id FROM books b, authors a 
WHERE b.isbn = '978-5-17-070490-3' 
  AND a.first_name = 'Лев' AND a.last_name = 'Толстой'
ON CONFLICT (book_id, author_id) DO NOTHING;

-- Связываем книгу с категорией
INSERT INTO book_categories (book_id, category_id) 
SELECT b.id, c.id FROM books b, categories c 
WHERE b.isbn = '978-5-17-070490-3' 
  AND c.name = 'Художественная литература'
ON CONFLICT (book_id, category_id) DO NOTHING;