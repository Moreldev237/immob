/**
 * IMMOB Frontend - Backend Integration
 * Connects to Django REST API at http://127.0.0.1:8001/
 */

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8001';

// Axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_BASE_URL}/api/token/refresh/`, {
                        refresh: refreshToken
                    });
                    
                    localStorage.setItem('access_token', response.data.access);
                    originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
                    return api(originalRequest);
                } catch (refreshError) {
                    // Refresh failed, logout user
                    logout();
                    return Promise.reject(refreshError);
                }
            }
        }
        return Promise.reject(error);
    }
);

// ==================== AUTH SERVICE ====================

const AuthService = {
    async login(email, password) {
        const response = await api.post('/api/users/login/', { email, password });
        return response.data;
    },

    async register(userData) {
        const response = await api.post('/api/users/', userData);
        return response.data;
    },

    async logout() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            try {
                await api.post('/api/users/logout/', { refresh_token: refreshToken });
            } catch (error) {
                console.error('Logout error:', error);
            }
        }
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },

    async getProfile() {
        const response = await api.get('/api/users/profile/');
        return response.data;
    },

    async requestPasswordReset(email) {
        const response = await api.post('/api/users/password_reset/', { email });
        return response.data;
    },

    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    },

    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }
};

// ==================== PROPERTIES SERVICE ====================

const PropertiesService = {
    async getAll(params = {}) {
        const response = await api.get('/api/properties/properties/', { params });
        return response.data;
    },

    async getById(id) {
        const response = await api.get(`/api/properties/properties/${id}/`);
        return response.data;
    },

    async getFeatured() {
        const response = await api.get('/api/properties/properties/featured/');
        return response.data;
    },

    async getCategories() {
        const response = await api.get('/api/properties/properties/categories/');
        return response.data;
    },

    async toggleFavorite(propertyId) {
        const response = await api.post('/api/properties/favorites/', { property_id: propertyId });
        return response.data;
    },

    async getFavorites() {
        const response = await api.get('/api/properties/favorites/');
        return response.data;
    },

    async checkFavorite(propertyId) {
        const response = await api.get('/api/properties/favorites/check/', { 
            params: { property_id: propertyId } 
        });
        return response.data;
    },

    async getStats() {
        const response = await api.get('/api/properties/properties/stats/');
        return response.data;
    }
};

// ==================== REVIEWS SERVICE ====================

const ReviewsService = {
    async getAll(params = {}) {
        const response = await api.get('/api/reviews/reviews/', { params });
        return response.data;
    },

    async create(data) {
        const response = await api.post('/api/reviews/reviews/', data);
        return response.data;
    },

    async submitFeedback(data) {
        const response = await api.post('/api/reviews/feedback/', data);
        return response.data;
    },

    async getMyReviews() {
        const response = await api.get('/api/reviews/reviews/my_reviews/');
        return response.data;
    }
};

// ==================== UI HELPERS ====================

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.style.backgroundColor = type === 'error' ? '#ef4444' : '#10b981';
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

function formatPrice(price, isRental = false) {
    const formatted = new Intl.NumberFormat('fr-FR').format(price);
    return isRental ? `${formatted} FCFA/mois` : `${formatted} FCFA`;
}

function getStatusLabel(status) {
    const labels = {
        'for_sale': 'À vendre',
        'for_rent': 'À louer',
        'sold': 'Vendu',
        'rented': 'Louée'
    };
    return labels[status] || status;
}

function getStatusClass(status) {
    return status === 'for_rent' ? 'bg-green-600' : 'bg-blue-600';
}

// ==================== RENDER FUNCTIONS ====================

function renderPropertyCard(property) {
    const isRental = property.status === 'for_rent';
    const imageUrl = property.images && property.images.length > 0 
        ? property.images[0].image 
        : 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80';
    
    return `
        <div class="property-card bg-white rounded-xl shadow-lg overflow-hidden" data-id="${property.id}">
            <div class="relative">
                <img src="${imageUrl}" alt="${property.title}" class="w-full property-image" onerror="this.src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'">
                <div class="absolute top-4 right-4 ${getStatusClass(property.status)} text-white px-3 py-1 rounded-full font-bold">
                    ${getStatusLabel(property.status)}
                </div>
                <button class="favorite-btn absolute top-4 left-4 bg-white p-2 rounded-full text-red-500 hover:text-red-700 transition" data-id="${property.id}">
                    <i class="far fa-heart"></i>
                </button>
            </div>
            <div class="p-6">
                <h3 class="text-xl font-bold mb-2">${property.title}</h3>
                <p class="text-gray-600 mb-4">${property.description ? property.description.substring(0, 100) + '...' : 'Aucune description disponible'}</p>
                <div class="flex justify-between items-center mb-4">
                    <div class="text-blue-600 font-bold text-2xl">${formatPrice(property.price, isRental)}</div>
                    <div class="flex items-center text-gray-600">
                        <i class="fas fa-bed mr-1"></i> ${property.bedrooms || 0}
                        <i class="fas fa-bath ml-4 mr-1"></i> ${property.bathrooms || 0}
                        <i class="fas fa-ruler-combined ml-4 mr-1"></i> ${property.area || 0}m²
                    </div>
                </div>
                <button class="btn-primary w-full view-details-btn" data-id="${property.id}">
                    <i class="fas fa-eye mr-2"></i>Voir les détails
                </button>
            </div>
        </div>
    `;
}

function renderTestimonialCard(review) {
    const user = review.user || {};
    const initials = user.first_name ? user.first_name[0] : 'U';
    
    return `
        <div class="testimonial-card p-6 rounded-xl shadow-lg">
            <div class="flex items-center mb-4">
                <div class="w-12 h-12 rounded-full bg-blue-200 flex items-center justify-center mr-4">
                    <span class="font-bold text-blue-700">${initials}</span>
                </div>
                <div>
                    <h4 class="font-bold">${user.first_name || 'Utilisateur'} ${user.last_name || ''}</h4>
                    <div class="flex text-yellow-400">
                        ${Array(5).fill(0).map((_, i) => 
                            `<i class="fas fa-star ${i < review.rating ? '' : 'text-gray-300'}"></i>`
                        ).join('')}
                    </div>
                </div>
            </div>
            <p class="text-gray-700 italic">"${review.comment || review.content || 'Excellent service!'}"</p>
        </div>
    `;
}

function renderLoadingSpinner() {
    return `
        <div class="flex justify-center items-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
    `;
}

function renderErrorMessage(message) {
    return `
        <div class="text-center py-12">
            <i class="fas fa-exclamation-triangle text-4xl text-yellow-500 mb-4"></i>
            <p class="text-gray-600">${message || 'Une erreur est survenue'}</p>
            <button onclick="loadProperties()" class="mt-4 btn-primary">Réessayer</button>
        </div>
    `;
}

function renderEmptyState(message) {
    return `
        <div class="text-center py-12">
            <i class="fas fa-home text-4xl text-gray-400 mb-4"></i>
            <p class="text-gray-600">${message || 'Aucun bien trouvé'}</p>
        </div>
    `;
}

// ==================== LOAD DATA FUNCTIONS ====================

async function loadProperties() {
    const container = document.querySelector('#properties .grid');
    if (!container) return;
    
    container.innerHTML = renderLoadingSpinner();
    
    try {
        const params = {
            status: 'for_sale,for_rent',
            ordering: '-created_at'
        };
        
        // Add filters from search form
        const propertyType = document.querySelector('select:nth-of-type(1)')?.value;
        const location = document.querySelector('select:nth-of-type(2)')?.value;
        const maxPrice = document.querySelector('select:nth-of-type(3)')?.value;
        
        if (propertyType && propertyType !== 'Tous les types') {
            params.property_type__name = propertyType;
        }
        
        if (location && location !== 'Partout') {
            params.location__city = location;
        }
        
        if (maxPrice && maxPrice !== 'Illimité') {
            const priceMap = {
                '5,000,000': 5000000,
                '10,000,000': 10000000,
                '20,000,000': 20000000,
                '50,000,000': 50000000,
                '100,000,000': 100000000
            };
            params.price__lte = priceMap[maxPrice] || maxPrice;
        }
        
        const response = await PropertiesService.getAll(params);
        const properties = response.results || response;
        
        if (properties.length === 0) {
            container.innerHTML = renderEmptyState('Aucun bien ne correspond à vos critères');
            return;
        }
        
        container.innerHTML = properties.slice(0, 6).map(renderPropertyCard).join('');
        
        // Add event listeners to favorite buttons
        attachFavoriteListeners();
        attachViewDetailsListeners();
        
    } catch (error) {
        console.error('Error loading properties:', error);
        container.innerHTML = renderErrorMessage('Impossible de charger les biens. Vérifiez que le serveur est en cours d\'exécution.');
    }
}

async function loadTestimonials() {
    const container = document.querySelector('#testimonials .grid');
    if (!container) return;
    
    try {
        const reviews = await ReviewsService.getAll({ is_approved: true });
        
        if (reviews.length === 0) {
            // Keep static testimonials if no reviews from API
            return;
        }
        
        container.innerHTML = reviews.slice(0, 3).map(renderTestimonialCard).join('');
        
    } catch (error) {
        console.error('Error loading reviews:', error);
        // Keep static testimonials on error
    }
}

async function updateAuthUI() {
    const loginBtn = document.getElementById('login-btn');
    if (!loginBtn) return;
    
    if (AuthService.isAuthenticated()) {
        const user = AuthService.getUser();
        loginBtn.innerHTML = `<i class="fas fa-user mr-2"></i>${user?.first_name || 'Mon compte'}`;
        loginBtn.classList.remove('btn-secondary');
        loginBtn.classList.add('btn-primary');
        
        // Add logout button if not exists
        if (!document.getElementById('logout-btn')) {
            const logoutBtn = document.createElement('button');
            logoutBtn.id = 'logout-btn';
            logoutBtn.className = 'bg-red-500 text-white font-bold py-2 px-4 rounded-lg hover:bg-red-600 transition ml-4';
            logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt mr-2"></i>Déconnexion';
            logoutBtn.addEventListener('click', handleLogout);
            loginBtn.parentNode.appendChild(logoutBtn);
        }
    } else {
        loginBtn.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Connexion';
        loginBtn.classList.add('btn-secondary');
        loginBtn.classList.remove('btn-primary');
        
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) logoutBtn.remove();
    }
}

// ==================== EVENT HANDLERS ====================

function attachFavoriteListeners() {
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            
            if (!AuthService.isAuthenticated()) {
                showToast('Veuillez vous connecter pour ajouter aux favoris', 'error');
                document.getElementById('login-modal').style.display = 'block';
                return;
            }
            
            const propertyId = btn.dataset.id;
            const icon = btn.querySelector('i');
            
            try {
                const result = await PropertiesService.toggleFavorite(propertyId);
                
                if (result.is_favorited) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    showToast('Ajouté aux favoris');
                } else {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    showToast('Retiré des favoris');
                }
            } catch (error) {
                console.error('Favorite error:', error);
                showToast('Erreur lors de la mise à jour des favoris', 'error');
            }
        });
    });
}

function attachViewDetailsListeners() {
    document.querySelectorAll('.view-details-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const propertyId = btn.dataset.id;
            // In a real app, this would open a detail page/modal
            showToast(`Chargement des détails du bien #${propertyId}...`);
            // window.location.href = `/property/${propertyId}`;
        });
    });
}

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const rememberMe = document.getElementById('remember-me').checked;
    
    try {
        const data = await AuthService.login(email, password);
        
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user || {}));
        
        showToast('Connexion réussie!');
        
        setTimeout(() => {
            document.getElementById('login-modal').style.display = 'none';
            updateAuthUI();
        }, 1000);
        
    } catch (error) {
        console.error('Login error:', error);
        const message = error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || 'Échec de la connexion';
        showToast(message, 'error');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const firstName = document.getElementById('signup-firstname').value;
    const lastName = document.getElementById('signup-lastname').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;
    
    if (password !== confirmPassword) {
        showToast('Les mots de passe ne correspondent pas', 'error');
        return;
    }
    
    if (password.length < 8) {
        showToast('Le mot de passe doit contenir au moins 8 caractères', 'error');
        return;
    }
    
    try {
        await AuthService.register({
            email,
            password,
            first_name: firstName,
            last_name: lastName
        });
        
        // Auto login after registration
        const data = await AuthService.login(email, password);
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user || {}));
        
        showToast('Compte créé avec succès!');
        
        setTimeout(() => {
            document.getElementById('signup-modal').style.display = 'none';
            updateAuthUI();
        }, 1000);
        
    } catch (error) {
        console.error('Signup error:', error);
        const message = error.response?.data?.email?.[0] || error.response?.data?.password?.[0] || 
                       error.response?.data?.non_field_errors?.[0] || 'Échec de l\'inscription';
        showToast(message, 'error');
    }
}

async function handleLogout() {
    try {
        await AuthService.logout();
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    showToast('Déconnexion réussie');
    
    setTimeout(() => {
        updateAuthUI();
    }, 1000);
}

async function handlePasswordReset(e) {
    e.preventDefault();
    
    const email = document.getElementById('reset-email').value;
    
    try {
        await AuthService.requestPasswordReset(email);
        showToast('Un lien de réinitialisation a été envoyé à votre adresse email');
        
        setTimeout(() => {
            document.getElementById('forgot-password-modal').style.display = 'none';
            document.getElementById('login-modal').style.display = 'block';
        }, 1500);
        
    } catch (error) {
        console.error('Password reset error:', error);
        showToast('Erreur lors de l\'envoi du lien de réinitialisation', 'error');
    }
}

async function handleFeedback(e) {
    e.preventDefault();
    
    const rating = document.getElementById('rating-value').value;
    const comment = document.getElementById('feedback-text').value;
    
    if (rating === '0') {
        showToast('Veuillez donner une note', 'error');
        return;
    }
    
    if (comment.trim() === '') {
        showToast('Veuillez écrire votre avis', 'error');
        return;
    }
    
    try {
        await ReviewsService.submitFeedback({
            title: 'Feedback via le site web',
            comment: comment,
            rating: parseInt(rating)
        });
        
        showToast('Merci pour votre avis!');
        
        // Reset form
        document.getElementById('rating-value').value = '0';
        document.getElementById('feedback-text').value = '';
        
        document.querySelectorAll('.rating-star').forEach(star => {
            star.classList.remove('fas');
            star.classList.add('far');
        });
        
    } catch (error) {
        console.error('Feedback error:', error);
        showToast('Erreur lors de l\'envoi de l\'avis', 'error');
    }
}

function handleSearch(e) {
    if (e.key === 'Enter') {
        const query = e.target.value.trim();
        if (query) {
            showToast(`Recherche de "${query}" en cours...`);
            // In a real app: window.location.href = `/search?q=${query}`;
        }
    }
}

function handleAdvancedSearch() {
    showToast('Recherche en cours...');
    loadProperties();
}

// ==================== INITIALIZATION ====================

function initModals() {
    const loginModal = document.getElementById('login-modal');
    const signupModal = document.getElementById('signup-modal');
    const forgotPasswordModal = document.getElementById('forgot-password-modal');
    const cookieModal = document.getElementById('cookie-modal');
    const loginBtn = document.getElementById('login-btn');
    const signupBtn = document.getElementById('signup-btn');
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    const showSignup = document.getElementById('show-signup');
    const showLogin = document.getElementById('show-login');
    const backToLogin = document.getElementById('back-to-login');
    const closeModalButtons = document.querySelectorAll('.close-modal');
    const cookieSettingsBtn = document.getElementById('cookie-settings');
    
    if (loginBtn) loginBtn.addEventListener('click', () => loginModal.style.display = 'block');
    if (signupBtn) signupBtn.addEventListener('click', () => signupModal.style.display = 'block');
    
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginModal.style.display = 'none';
            forgotPasswordModal.style.display = 'block';
        });
    }
    
    if (showSignup) {
        showSignup.addEventListener('click', (e) => {
            e.preventDefault();
            loginModal.style.display = 'none';
            signupModal.style.display = 'block';
        });
    }
    
    if (showLogin) {
        showLogin.addEventListener('click', (e) => {
            e.preventDefault();
            signupModal.style.display = 'none';
            loginModal.style.display = 'block';
        });
    }
    
    if (backToLogin) {
        backToLogin.addEventListener('click', (e) => {
            e.preventDefault();
            forgotPasswordModal.style.display = 'none';
            loginModal.style.display = 'block';
        });
    }
    
    if (cookieSettingsBtn) {
        cookieSettingsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            cookieModal.style.display = 'block';
        });
    }
    
    closeModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            loginModal.style.display = 'none';
            signupModal.style.display = 'none';
            forgotPasswordModal.style.display = 'none';
            cookieModal.style.display = 'none';
        });
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === loginModal) loginModal.style.display = 'none';
        if (e.target === signupModal) signupModal.style.display = 'none';
        if (e.target === forgotPasswordModal) forgotPasswordModal.style.display = 'none';
        if (e.target === cookieModal) cookieModal.style.display = 'none';
    });
}

function initRatingStars() {
    const ratingStars = document.querySelectorAll('.rating-star');
    const ratingValue = document.getElementById('rating-value');
    
    ratingStars.forEach(star => {
        star.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            ratingValue.value = value;
            
            ratingStars.forEach(s => {
                if (s.getAttribute('data-value') <= value) {
                    s.classList.remove('far');
                    s.classList.add('fas');
                } else {
                    s.classList.remove('fas');
                    s.classList.add('far');
                }
            });
        });
    });
}

function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

function initForms() {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    const feedbackForm = document.getElementById('feedback-form');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.querySelector('.btn-primary');
    
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (signupForm) signupForm.addEventListener('submit', handleSignup);
    if (forgotPasswordForm) forgotPasswordForm.addEventListener('submit', handlePasswordReset);
    if (feedbackForm) feedbackForm.addEventListener('submit', handleFeedback);
    if (searchInput) searchInput.addEventListener('keyup', handleSearch);
    if (searchBtn) searchBtn.addEventListener('click', handleAdvancedSearch);
}

function initCookieSettings() {
    const acceptAllCookiesBtn = document.getElementById('accept-all-cookies');
    const saveCookiePreferencesBtn = document.getElementById('save-cookie-preferences');
    const toggleSwitches = document.querySelectorAll('.toggle-switch');
    
    if (acceptAllCookiesBtn) {
        acceptAllCookiesBtn.addEventListener('click', () => {
            document.getElementById('performance-cookies').checked = true;
            document.getElementById('marketing-cookies').checked = true;
            
            toggleSwitches.forEach(switchEl => {
                switchEl.style.backgroundColor = '#3b82f6';
            });
            
            showToast('Tous les cookies ont été acceptés');
            setTimeout(() => {
                document.getElementById('cookie-modal').style.display = 'none';
            }, 1000);
        });
    }
    
    if (saveCookiePreferencesBtn) {
        saveCookiePreferencesBtn.addEventListener('click', () => {
            showToast('Préférences de cookies enregistrées');
            setTimeout(() => {
                document.getElementById('cookie-modal').style.display = 'none';
            }, 1000);
        });
    }
    
    toggleSwitches.forEach(switchEl => {
        switchEl.addEventListener('click', function() {
            const checkbox = document.getElementById(this.getAttribute('for'));
            checkbox.checked = !checkbox.checked;
            this.style.backgroundColor = checkbox.checked ? '#3b82f6' : '#d1d5db';
        });
    });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('IMMOB Frontend initializing...');
    console.log('API Base URL:', API_BASE_URL);
    
    // Initialize UI components
    initModals();
    initRatingStars();
    initMobileMenu();
    initForms();
    initCookieSettings();
    
    // Load data from API
    await loadProperties();
    await loadTestimonials();
    
    // Update auth UI
    updateAuthUI();
    
    console.log('IMMOB Frontend ready!');
});

