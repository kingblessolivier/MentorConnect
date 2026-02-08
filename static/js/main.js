/**
 * MentorConnect - Main JavaScript
 * Handles interactivity, accessibility, and dynamic features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavbar();
    initDropdowns();
    initToasts();
    initModals();
    initAccessibility();
    initNotifications();
    initForms();
});

/**
 * Navbar Toggle for Mobile
 */
function initNavbar() {
    const toggle = document.getElementById('navbarToggle');
    const menu = document.getElementById('navbarMenu');

    if (toggle && menu) {
        toggle.addEventListener('click', function() {
            menu.classList.toggle('active');
            const isExpanded = menu.classList.contains('active');
            toggle.setAttribute('aria-expanded', isExpanded);
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!toggle.contains(e.target) && !menu.contains(e.target)) {
                menu.classList.remove('active');
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
    }
}

/**
 * Dropdown Menus
 */
function initDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown');

    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');

        if (toggle) {
            toggle.addEventListener('click', function(e) {
                e.stopPropagation();

                // Close other dropdowns
                dropdowns.forEach(d => {
                    if (d !== dropdown) d.classList.remove('active');
                });

                dropdown.classList.toggle('active');
            });
        }
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        dropdowns.forEach(d => d.classList.remove('active'));
    });
}

/**
 * Toast Notifications
 */
function initToasts() {
    const toasts = document.querySelectorAll('.toast');

    toasts.forEach(toast => {
        const closeBtn = toast.querySelector('.toast-close');
        const autohide = toast.dataset.autohide;

        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismissToast(toast));
        }

        if (autohide) {
            setTimeout(() => dismissToast(toast), parseInt(autohide));
        }
    });
}

function dismissToast(toast) {
    toast.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i data-feather="${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close" aria-label="Close">&times;</button>
    `;

    container.appendChild(toast);
    feather.replace();

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => dismissToast(toast));

    setTimeout(() => dismissToast(toast), 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    container.setAttribute('role', 'alert');
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'alert-circle',
        warning: 'alert-triangle',
        info: 'info'
    };
    return icons[type] || 'info';
}

/**
 * Modal Dialogs
 */
function initModals() {
    const modalTriggers = document.querySelectorAll('[data-modal]');

    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.dataset.modal;
            const modal = document.getElementById(modalId);
            if (modal) openModal(modal);
        });
    });

    // Close modal on overlay click or close button
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) closeModal(this);
        });

        const closeBtn = overlay.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => closeModal(overlay));
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal-overlay.active');
            if (activeModal) closeModal(activeModal);
        }
    });
}

function openModal(modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Focus first focusable element
    const focusable = modal.querySelector('input, button, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable) focusable.focus();
}

function closeModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

/**
 * Accessibility Features
 */
function initAccessibility() {
    // Apply saved settings on page load first
    applyAccessibilitySettings();

    const toggleBtn = document.getElementById('accessibilityToggle');
    const panel = document.getElementById('accessibilityPanel');
    const overlay = document.getElementById('accessibilityOverlay');
    const closeBtn = document.getElementById('accessibilityClose');

    // Debug log
    console.log('Accessibility init:', { toggleBtn, panel, overlay, closeBtn });

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Accessibility toggle clicked');

            if (panel) {
                const isActive = panel.classList.contains('active');
                if (isActive) {
                    closeAccessibilityPanel();
                } else {
                    openAccessibilityPanel();
                }
            }
        });
    }

    // Close button
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeAccessibilityPanel();
        });
    }

    // Close on overlay click
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            e.preventDefault();
            closeAccessibilityPanel();
        });
    }

    // High Contrast Toggle
    const highContrastToggle = document.getElementById('highContrastToggle');
    if (highContrastToggle) {
        highContrastToggle.addEventListener('change', function() {
            toggleHighContrast(this.checked);
            saveAccessibilitySetting('high_contrast', this.checked);
        });
    }

    // Large Font Toggle
    const largeFontToggle = document.getElementById('largeFontToggle');
    if (largeFontToggle) {
        largeFontToggle.addEventListener('change', function() {
            toggleLargeText(this.checked);
            saveAccessibilitySetting('large_text', this.checked);
        });
    }

    // Text-to-Speech Toggle
    const ttsToggle = document.getElementById('ttsToggle');
    if (ttsToggle) {
        ttsToggle.addEventListener('change', function() {
            toggleTextToSpeech(this.checked);
            saveAccessibilitySetting('text_to_speech', this.checked);
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const panel = document.getElementById('accessibilityPanel');
            if (panel && panel.classList.contains('active')) {
                closeAccessibilityPanel();
            }
        }
    });
}

function openAccessibilityPanel() {
    const panel = document.getElementById('accessibilityPanel');
    const overlay = document.getElementById('accessibilityOverlay');
    const toggleBtn = document.getElementById('accessibilityToggle');

    if (panel) {
        panel.classList.add('active');
        panel.setAttribute('aria-hidden', 'false');
    }
    if (overlay) overlay.classList.add('active');
    if (toggleBtn) toggleBtn.classList.add('active');

    // Re-init feather icons in panel
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function closeAccessibilityPanel() {
    const panel = document.getElementById('accessibilityPanel');
    const overlay = document.getElementById('accessibilityOverlay');
    const toggleBtn = document.getElementById('accessibilityToggle');

    if (panel) {
        panel.classList.remove('active');
        panel.setAttribute('aria-hidden', 'true');
    }
    if (overlay) overlay.classList.remove('active');
    if (toggleBtn) toggleBtn.classList.remove('active');
}

function applyAccessibilitySettings() {
    // Check localStorage for settings
    const highContrast = localStorage.getItem('accessibility_high_contrast') === 'true';
    const largeText = localStorage.getItem('accessibility_large_text') === 'true';
    const tts = localStorage.getItem('accessibility_text_to_speech') === 'true';

    // Apply settings
    if (highContrast) toggleHighContrast(true);
    if (largeText) toggleLargeText(true);
    if (tts) toggleTextToSpeech(true);

    // Update checkboxes
    const highContrastToggle = document.getElementById('highContrastToggle');
    const largeFontToggle = document.getElementById('largeFontToggle');
    const ttsToggle = document.getElementById('ttsToggle');

    if (highContrastToggle) highContrastToggle.checked = highContrast;
    if (largeFontToggle) largeFontToggle.checked = largeText;
    if (ttsToggle) ttsToggle.checked = tts;
}

function toggleHighContrast(enabled) {
    if (enabled) {
        document.body.classList.add('high-contrast');
    } else {
        document.body.classList.remove('high-contrast');
    }
}

function toggleLargeText(enabled) {
    if (enabled) {
        document.body.classList.add('large-text');
    } else {
        document.body.classList.remove('large-text');
    }
}

function toggleTextToSpeech(enabled) {
    if (enabled) {
        document.body.classList.add('tts-enabled');
        initTextToSpeech();
    } else {
        document.body.classList.remove('tts-enabled');
        // Cancel any ongoing speech
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        // Remove TTS event listeners
        document.querySelectorAll('.tts-readable').forEach(el => {
            el.classList.remove('tts-readable');
            el.removeAttribute('tabindex');
        });
    }
}

function saveAccessibilitySetting(setting, value) {
    // Save to localStorage for immediate persistence
    localStorage.setItem('accessibility_' + setting, value);

    // Also save to server session
    fetch(`/set-accessibility/?setting=${setting}&value=${value}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show feedback
            showToast(value ? `${formatSettingName(setting)} enabled` : `${formatSettingName(setting)} disabled`, 'success');
        }
    })
    .catch(err => console.error('Error saving accessibility setting:', err));
}

function formatSettingName(setting) {
    const names = {
        'high_contrast': 'High Contrast',
        'large_text': 'Large Text',
        'text_to_speech': 'Text-to-Speech'
    };
    return names[setting] || setting;
}

/**
 * Text-to-Speech for Accessibility
 */
function initTextToSpeech() {
    if (!('speechSynthesis' in window)) {
        console.warn('Text-to-Speech not supported in this browser');
        showToast('Text-to-Speech is not supported in your browser', 'warning');
        return;
    }

    // Add TTS to readable elements
    const readableSelectors = 'p, h1, h2, h3, h4, h5, h6, li, .card-title, .card-text, .post-content, blockquote, figcaption, label';
    const readableElements = document.querySelectorAll(readableSelectors);

    readableElements.forEach(el => {
        // Skip if already has TTS
        if (el.classList.contains('tts-readable')) return;

        // Skip empty elements or elements with only whitespace
        if (!el.textContent.trim()) return;

        el.classList.add('tts-readable');
        el.setAttribute('tabindex', '0');
        el.setAttribute('role', 'button');
        el.setAttribute('aria-label', 'Click to hear this text');

        el.addEventListener('click', handleTTSClick);
        el.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleTTSClick.call(this, e);
            }
        });
    });
}

function handleTTSClick(e) {
    e.stopPropagation();
    const text = this.textContent.trim();

    // Remove speaking class from all elements
    document.querySelectorAll('.tts-speaking').forEach(el => {
        el.classList.remove('tts-speaking');
    });

    // Add speaking class to current element
    this.classList.add('tts-speaking');

    speak(text, () => {
        this.classList.remove('tts-speaking');
    });
}

function speak(text, onEnd) {
    if (!('speechSynthesis' in window)) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;

    // Try to use a good voice
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
        || voices.find(v => v.lang.startsWith('en'));
    if (preferredVoice) {
        utterance.voice = preferredVoice;
    }

    utterance.onend = onEnd;
    utterance.onerror = onEnd;

    window.speechSynthesis.speak(utterance);
}

/**
 * Notifications
 */
function initNotifications() {
    updateNotificationCount();
    loadRecentNotifications();

    // Update every 30 seconds
    setInterval(updateNotificationCount, 30000);
}

function updateNotificationCount() {
    fetch('/notifications/count/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            badge.textContent = data.count;
            badge.style.display = data.count > 0 ? 'flex' : 'none';
        }
    })
    .catch(err => console.error('Error:', err));
}

function loadRecentNotifications() {
    const list = document.getElementById('notificationList');
    if (!list) return;

    fetch('/notifications/recent/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.notifications && data.notifications.length > 0) {
            list.innerHTML = data.notifications.map(n => `
                <div class="notification-item ${n.is_read ? '' : 'unread'}">
                    <i data-feather="${n.icon}"></i>
                    <div>
                        <p class="text-sm">${n.message}</p>
                        <span class="text-muted text-sm">${n.created_at}</span>
                    </div>
                </div>
            `).join('');
            feather.replace();
        }
    })
    .catch(err => console.error('Error:', err));
}

/**
 * Form Enhancements
 */
function initForms() {
    // Auto-resize textareas
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });

    // Form validation styling
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span> Loading...';
            }
        });
    });

    // File input preview
    document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
        input.addEventListener('change', function() {
            const preview = this.closest('.form-group').querySelector('.image-preview');
            if (preview && this.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    preview.src = e.target.result;
                    preview.hidden = false;
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
}

/**
 * Loading Overlay
 */
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('active');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
}

/**
 * AJAX Helper
 */
function fetchAPI(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    };

    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        defaultOptions.headers['X-CSRFToken'] = csrfToken.value;
    }

    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        });
}

/**
 * Like Button Handler
 */
function toggleLike(postId) {
    fetchAPI(`/feed/post/${postId}/like/`, { method: 'POST' })
        .then(data => {
            const btn = document.querySelector(`[data-post-id="${postId}"] .like-btn`);
            const count = document.querySelector(`[data-post-id="${postId}"] .likes-count`);

            if (btn) {
                btn.classList.toggle('liked', data.liked);
            }
            if (count) {
                count.textContent = data.likes_count;
            }
        })
        .catch(err => showToast('Error liking post', 'error'));
}

/**
 * Follow Button Handler
 */
function toggleFollow(userId) {
    const btn = document.querySelector(`[data-user-id="${userId}"]`);
    const isFollowing = btn.classList.contains('following');
    const url = isFollowing ? `/profiles/unfollow/${userId}/` : `/profiles/follow/${userId}/`;

    fetchAPI(url, { method: 'POST' })
        .then(data => {
            btn.classList.toggle('following', data.following);
            btn.textContent = data.following ? 'Following' : 'Follow';

            const count = document.querySelector('.followers-count');
            if (count) count.textContent = data.followers_count;
        })
        .catch(err => showToast('Error', 'error'));
}

/**
 * Infinite Scroll (for feed)
 */
function initInfiniteScroll(containerSelector, loadMoreCallback) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    let loading = false;
    let page = 1;

    window.addEventListener('scroll', function() {
        if (loading) return;

        const { scrollTop, scrollHeight, clientHeight } = document.documentElement;

        if (scrollTop + clientHeight >= scrollHeight - 500) {
            loading = true;
            page++;

            loadMoreCallback(page)
                .then(() => { loading = false; })
                .catch(() => { loading = false; });
        }
    });
}

// Export for global use
window.MentorConnect = {
    showToast,
    showLoading,
    hideLoading,
    openModal,
    closeModal,
    toggleLike,
    toggleFollow,
    speak,
    fetchAPI
};
