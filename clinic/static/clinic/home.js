/**
 * ePetCare Home Page Interactivity
 * This script adds interactive elements to the home page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add data-aos attribute to elements for scroll animation
    const elementsToAnimate = document.querySelectorAll(
        '.feature-card, .step-card, .testimonial-card, .section-title, .section-header'
    );

    elementsToAnimate.forEach((el, index) => {
        if (!el.hasAttribute('data-aos')) {
            el.setAttribute('data-aos', 'fade-up');
            el.setAttribute('data-aos-duration', '800');
            el.setAttribute('data-aos-delay', (index % 3) * 100 + '');
            el.setAttribute('data-aos-once', 'true');
        }
    });

    // Initialize AOS library if it exists
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true
        });
    } else {
        // Fallback animation if AOS is not available
        initFallbackAnimations();
    }

    // Add parallax effect to hero section
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        window.addEventListener('scroll', function() {
            const scrollPosition = window.scrollY;
            if (scrollPosition < 600) {
                const translateY = scrollPosition * 0.2;
                heroSection.style.backgroundPosition = `50% ${translateY}px`;
            }
        });
    }

    // Add smooth scroll to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add hover effect to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            featureCards.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const x = e.clientX - e.target.getBoundingClientRect().left;
            const y = e.clientY - e.target.getBoundingClientRect().top;

            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;

            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// Fallback animation function if AOS library is not available
function initFallbackAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    document.querySelectorAll('[data-aos]').forEach(el => {
        el.classList.add('aos-animate-init');
        observer.observe(el);
    });
}

// Add ripple style dynamically if not already in the stylesheet
if (!document.querySelector('#rippleStyle')) {
    const style = document.createElement('style');
    style.id = 'rippleStyle';
    style.textContent = `
        .btn {
            position: relative;
            overflow: hidden;
        }
        .ripple {
            position: absolute;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
        }
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        .aos-animate-init {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        .aos-animate-init.in-view {
            opacity: 1;
            transform: translateY(0);
        }
    `;
    document.head.appendChild(style);
}