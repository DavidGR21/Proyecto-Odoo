/** @odoo-module **/
/**
 * VitalPet - JavaScript principal
 * Animaciones, navbar móvil y utilidades
 */

// =====================================================
// Intersection Observer - Animaciones al hacer scroll
// =====================================================
function initAnimations() {
    // Marcar el body para activar estados ocultos vía CSS
    document.body.classList.add('vp-js-ready');

    const elements = document.querySelectorAll('[data-vp-animate]');
    if (!elements.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const delay = parseInt(entry.target.dataset.vpDelay || '0', 10);
                    setTimeout(() => {
                        entry.target.classList.add('vp-animated');
                    }, delay);
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.08, rootMargin: '0px 0px -30px 0px' }
    );

    elements.forEach((el) => {
        // Si el elemento ya está en el viewport (hero), animarlo inmediatamente
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.classList.add('vp-animated');
        } else {
            observer.observe(el);
        }
    });
}

// =====================================================
// Navbar móvil (hamburger toggle)
// =====================================================
function initMobileNav() {
    const hamburger = document.querySelector('.vp-hamburger');
    const navLinks  = document.querySelector('.vp-nav-links');
    if (!hamburger || !navLinks) return;

    hamburger.addEventListener('click', () => {
        const isOpen = navLinks.classList.toggle('open');
        hamburger.setAttribute('aria-expanded', isOpen);
        hamburger.querySelectorAll('span').forEach((span, i) => {
            if (isOpen) {
                if (i === 0) span.style.transform = 'rotate(45deg) translate(5px, 5px)';
                if (i === 1) span.style.opacity = '0';
                if (i === 2) span.style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                span.style.transform = '';
                span.style.opacity  = '';
            }
        });
    });

    // Cerrar al hacer click en un enlace
    navLinks.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('open');
        });
    });
}

// =====================================================
// Navbar sticky - cambio de estilo al hacer scroll
// =====================================================
function initStickyNavbar() {
    const navbar = document.querySelector('.vp-navbar-main');
    if (!navbar) return;

    const handleScroll = () => {
        if (window.scrollY > 50) {
            navbar.style.boxShadow = '0 4px 30px rgba(0,0,0,0.12)';
        } else {
            navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.08)';
        }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
}

// =====================================================
// Contador animado para las estadísticas
// =====================================================
function animateCounter(el, target, duration) {
    let start = 0;
    const step = target / (duration / 16);
    const suffix = el.dataset.suffix || '';
    const prefix = el.dataset.prefix || '';

    const update = () => {
        start += step;
        if (start < target) {
            el.textContent = prefix + Math.floor(start).toLocaleString() + suffix;
            requestAnimationFrame(update);
        } else {
            el.textContent = prefix + target.toLocaleString() + suffix;
        }
    };
    requestAnimationFrame(update);
}

function initCounters() {
    const counters = document.querySelectorAll('[data-vp-counter]');
    if (!counters.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const el     = entry.target;
                    const target = parseInt(el.dataset.vpCounter, 10);
                    animateCounter(el, target, 1800);
                    observer.unobserve(el);
                }
            });
        },
        { threshold: 0.5 }
    );

    counters.forEach((el) => observer.observe(el));
}

// =====================================================
// Formulario de contacto - feedback visual
// =====================================================
function initContactForm() {
    const form = document.querySelector('.vp-contact-form');
    if (!form) return;

    const btn = form.querySelector('.vp-form-btn');
    if (!btn) return;

    form.addEventListener('submit', () => {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-circle-o-notch fa-spin me-2"></i> Enviando...';
    });
}

// =====================================================
// Active nav link según la ruta actual
// =====================================================
function initActiveNavLink() {
    const links = document.querySelectorAll('.vp-nav-link');
    const path  = window.location.pathname;

    links.forEach((link) => {
        const href = link.getAttribute('href');
        const isActive =
            (href === '/' && path === '/') ||
            (href !== '/' && path.startsWith(href));

        if (isActive) {
            link.classList.add('vp-nav-active');
        }
    });
}

// =====================================================
// Init cuando el DOM esté listo
// =====================================================
document.addEventListener('DOMContentLoaded', () => {
    initAnimations();
    initMobileNav();
    initStickyNavbar();
    initCounters();
    initContactForm();
    initActiveNavLink();
});
