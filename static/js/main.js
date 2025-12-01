// Main JavaScript file for the online library

// Global variables
let currentUser = null;
let authToken = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    checkAuthStatus();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize search functionality
    initializeSearch();
    
    // Load dynamic content on home page
    if (window.location.pathname === '/' || window.location.pathname === '/index') {
        loadHomePageContent();
    }
});

// Check authentication status
function checkAuthStatus() {
    authToken = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    
    if (authToken && userStr) {
        try {
            currentUser = JSON.parse(userStr);
            updateNavigationForLoggedInUser();
        } catch (e) {
            console.error('Error parsing user data:', e);
            logout();
        }
    }
}

// Update navigation for logged-in user
function updateNavigationForLoggedInUser() {
    const authLinks = document.getElementById('authLinks');
    const userMenu = document.getElementById('userMenu');
    
    if (authLinks && userMenu && currentUser) {
        authLinks.style.display = 'none';
        userMenu.style.display = 'block';
        
        // Update user menu items based on role
        const adminLink = document.getElementById('adminLink');
        if (adminLink) {
            adminLink.style.display = currentUser.role === 'admin' ? 'block' : 'none';
        }
    }
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    currentUser = null;
    authToken = null;
    window.location.href = '/';
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('#searchInput, #heroSearch');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                showSearchSuggestions(query, e.target);
            } else {
                hideSearchSuggestions(e.target);
            }
        });
        
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch(e.target.value.trim());
            }
        });
    });
}

// Show search suggestions
function showSearchSuggestions(query, inputElement) {
    // This would need to be implemented in the API
    // For now, we'll show a simple implementation
    
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'search-suggestions';
    
    // Mock suggestions
    const mockSuggestions = [
        { title: 'Война и мир', type: 'book' },
        { title: 'Лев Толстой', type: 'author' },
        { title: 'Классическая литература', type: 'category' }
    ];
    
    const filteredSuggestions = mockSuggestions.filter(s => 
        s.title.toLowerCase().includes(query.toLowerCase())
    );
    
    if (filteredSuggestions.length > 0) {
        suggestionsContainer.innerHTML = filteredSuggestions.map(s => `
            <div class="suggestion-item" onclick="selectSuggestion('${s.title}', '${s.type}')">
                <i class="fas fa-${getTypeIcon(s.type)}"></i> ${s.title}
                <small class="text-muted ms-2">${getTypeLabel(s.type)}</small>
            </div>
        `).join('');
        
        // Position the suggestions container
        const rect = inputElement.getBoundingClientRect();
        suggestionsContainer.style.position = 'absolute';
        suggestionsContainer.style.top = (rect.bottom - rect.top) + 'px';
        suggestionsContainer.style.left = '0';
        suggestionsContainer.style.right = '0';
        suggestionsContainer.style.zIndex = '1000';
        
        inputElement.parentElement.style.position = 'relative';
        inputElement.parentElement.appendChild(suggestionsContainer);
    }
}

// Hide search suggestions
function hideSearchSuggestions(inputElement) {
    const suggestions = inputElement.parentElement.querySelector('.search-suggestions');
    if (suggestions) {
        suggestions.remove();
    }
}

// Get type icon for suggestions
function getTypeIcon(type) {
    const icons = {
        'book': 'book',
        'author': 'user',
        'category': 'tag'
    };
    return icons[type] || 'search';
}

// Get type label for suggestions
function getTypeLabel(type) {
    const labels = {
        'book': 'Книга',
        'author': 'Автор',
        'category': 'Категория'
    };
    return labels[type] || type;
}

// Select search suggestion
function selectSuggestion(title, type) {
    const searchInput = document.querySelector('#searchInput, #heroSearch');
    if (searchInput) {
        searchInput.value = title;
        hideSearchSuggestions(searchInput);
        performSearch(title);
    }
}

// Perform search
function performSearch(query) {
    if (query) {
        window.location.href = `/catalog?search=${encodeURIComponent(query)}`;
    }
}

// Load home page content
function loadHomePageContent() {
    loadPopularCategories();
    loadNewArrivals();
    loadPopularBooks();
}

// Load popular categories
function loadPopularCategories() {
    fetch('/api/books/categories')
        .then(response => response.json())
        .then(categories => {
            const container = document.getElementById('popularCategories');
            if (container) {
                container.innerHTML = categories.slice(0, 6).map(category => `
                    <div class="col-md-4 mb-3">
                        <div class="card h-100 category-card">
                            <div class="card-body text-center">
                                <i class="fas fa-folder fa-3x text-primary mb-3"></i>
                                <h5 class="card-title">${category.name}</h5>
                                <p class="card-text text-muted">${category.description || 'Категория книг'}</p>
                                <a href="/catalog?category=${category.id}" class="btn btn-outline-primary btn-sm">Смотреть книги</a>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        })
        .catch(error => {
            console.error('Error loading categories:', error);
        });
}

// Load new arrivals
function loadNewArrivals() {
    fetch('/api/books?sort=newest&limit=6')
        .then(response => response.json())
        .then(books => {
            const container = document.getElementById('newArrivals');
            if (container) {
                container.innerHTML = books.map(book => createBookCard(book)).join('');
            }
        })
        .catch(error => {
            console.error('Error loading new arrivals:', error);
        });
}

// Load popular books
function loadPopularBooks() {
    fetch('/api/books?sort=popular&limit=6')
        .then(response => response.json())
        .then(books => {
            const container = document.getElementById('popularBooks');
            if (container) {
                container.innerHTML = books.map(book => createBookCard(book)).join('');
            }
        })
        .catch(error => {
            console.error('Error loading popular books:', error);
        });
}

// Create book card HTML
function createBookCard(book) {
    const rating = book.rating || 0;
    const stars = Array(5).fill(0).map((_, i) => 
        i < Math.floor(rating) ? 'fas fa-star' : 'far fa-star'
    ).join(' ');
    
    return `
        <div class="col-md-4 mb-4">
            <div class="card h-100 book-card">
                <div class="book-cover-placeholder">
                    <i class="fas fa-book"></i>
                </div>
                <div class="card-body">
                    <h5 class="card-title">${book.title}</h5>
                    <p class="card-text text-muted">
                        ${book.authors?.map(a => a.first_name + ' ' + a.last_name).join(', ') || 'Неизвестный автор'}
                    </p>
                    <div class="mb-2">
                        <span class="text-warning">${stars}</span>
                        <small class="text-muted">(${rating.toFixed(1)})</small>
                    </div>
                    <p class="card-text">${book.description ? book.description.substring(0, 100) + '...' : 'Описание отсутствует'}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <a href="/book/${book.id}" class="btn btn-primary btn-sm">Подробнее</a>
                        <div>
                            <button class="btn btn-outline-danger btn-sm" onclick="toggleFavorite(${book.id}, this)">
                                В избранное
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Toggle favorite book
async function toggleFavorite(bookId, source) {

    let button = null;
    if (source instanceof HTMLElement) {
        button = source.closest('button');
    } else {
        const evt = source || window.event;
        if (evt && evt.target) {
            button = evt.target.closest('button');
        }
    }

    if (!button) return;

    const icon = button.querySelector('i');
    const isCurrentlyFavorite = icon && icon.classList.contains('fas');

    try {
        if (isCurrentlyFavorite) {
            // Удаляем из избранного
            await apiCall(`/api/users/me/favorites/${bookId}`, {
                method: 'DELETE'
            });
            if (icon) {
                icon.classList.remove('fas');
                icon.classList.add('far');
            }
            button.classList.remove('btn-danger');
            button.classList.add('btn-outline-danger');
        } else {
            // Добавляем в избранное
            await apiCall(`/api/users/me/favorites/${bookId}`, {
                method: 'POST'
            });
            if (icon) {
                icon.classList.remove('far');
                icon.classList.add('fas');
            }
            button.classList.remove('btn-outline-danger');
            button.classList.add('btn-danger');
        }
    } catch (error) {
        console.error('Ошибка обновления избранного:', error);
        alert('Не удалось обновить избранное. Попробуйте позже.');
        throw error;
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Show loading spinner
function showLoading(container) {
    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
                <p class="mt-2 text-muted">Загрузка...</p>
            </div>
        `;
    }
}

// Show error message
function showError(container, message) {
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
}

// Show empty message
function showEmpty(container, message) {
    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                <p class="text-muted">${message}</p>
            </div>
        `;
    }
}

// Utility function for API calls
async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    };
    
    if (authToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (response.status === 401) {
            logout();
            throw new Error('Unauthorized');
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other files
window.LibraryApp = {
    logout,
    performSearch,
    toggleFavorite,
    formatDate,
    formatFileSize,
    showLoading,
    showError,
    showEmpty,
    apiCall,
    debounce
};
