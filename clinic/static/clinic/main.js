/**
 * ePetCare Main JavaScript
 * Handles interactive UI elements and enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Toast notifications
    initToastNotifications();

    // Mobile navigation
    initMobileNavigation();

    // Form validation
    initFormValidation();

    // Initialize any filter functionality
    initFilters();

    // Card hover effects
    initCardEffects();
});

/**
 * Initialize toast notification functionality
 */
function initToastNotifications() {
    const toasts = document.querySelectorAll('.toast');

    // Add click handler to close buttons
    document.querySelectorAll('.toast-close').forEach(button => {
        button.addEventListener('click', function() {
            const toast = this.parentElement;
            toast.classList.add('toast-hiding');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
    });

    // Auto-dismiss after 5 seconds
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.classList.add('toast-hiding');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 5000);
    });
}

/**
 * Initialize mobile navigation
 */
function initMobileNavigation() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.getElementById('main-nav');

    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            menuToggle.classList.toggle('active');
            mainNav.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });

        // Close menu when clicking a link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function() {
                menuToggle.classList.remove('active');
                mainNav.classList.remove('active');
                document.body.classList.remove('menu-open');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (mainNav.classList.contains('active') &&
                !mainNav.contains(event.target) &&
                !menuToggle.contains(event.target)) {
                menuToggle.classList.remove('active');
                mainNav.classList.remove('active');
                document.body.classList.remove('menu-open');
            }
        });
    }
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        const requiredFields = form.querySelectorAll('[required]');

        form.addEventListener('submit', function(event) {
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');

                    // Create error message if it doesn't exist
                    let errorMsg = field.parentElement.querySelector('.error-message');
                    if (!errorMsg) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-message';
                        errorMsg.textContent = 'This field is required';
                        field.parentElement.appendChild(errorMsg);
                    }
                } else {
                    field.classList.remove('error');
                    const errorMsg = field.parentElement.querySelector('.error-message');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }
            });

            if (!isValid) {
                event.preventDefault();
            }
        });

        // Clear error state on input
        requiredFields.forEach(field => {
            field.addEventListener('input', function() {
                if (field.value.trim()) {
                    field.classList.remove('error');
                    const errorMsg = field.parentElement.querySelector('.error-message');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }
            });
        });
    });
}

/**
 * Initialize filters functionality
 */
function initFilters() {
    // Status filter for appointments
    const statusFilter = document.getElementById('status-filter');
    const dateFilter = document.getElementById('date-range');
    const appointmentCards = document.querySelectorAll('.appointment-card');
    const appointmentRows = document.querySelectorAll('.appointment-table tbody tr');

    function filterAppointments() {
        if (!statusFilter || !appointmentCards.length) return;

        const statusValue = statusFilter.value;
        const dateValue = dateFilter ? dateFilter.value : 'all';

        // Filter cards
        appointmentCards.forEach(card => {
            const status = card.dataset.status;
            let showCard = true;

            if (statusValue !== 'all' && status !== statusValue) {
                showCard = false;
            }

            card.style.display = showCard ? 'block' : 'none';
        });

        // Filter table rows
        appointmentRows.forEach(row => {
            if (row.classList.contains('empty-row')) return;

            const status = row.querySelector('.badge').textContent.toLowerCase();
            let showRow = true;

            if (statusValue !== 'all' && !status.includes(statusValue)) {
                showRow = false;
            }

            row.style.display = showRow ? '' : 'none';
        });
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', filterAppointments);
    }

    if (dateFilter) {
        dateFilter.addEventListener('change', filterAppointments);
    }
}

/**
 * Initialize card hover effects
 */
function initCardEffects() {
    const cards = document.querySelectorAll('.card, .appointment-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('card-hover');
        });

        card.addEventListener('mouseleave', function() {
            this.classList.remove('card-hover');
        });
    });
}