/**
 * Freedom Stream - Основной JavaScript
 * UX/UI улучшения: прогресс-бар, toast-уведомления, мобильное меню, тёмная тема
 */

// ===== TOAST УВЕДОМЛЕНИЯ =====
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Создаём контейнер для тостов
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        this.container.id = 'toastContainer';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${this.getIcon(type)}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
        `;

        this.container.appendChild(toast);

        // Анимация появления
        requestAnimationFrame(() => {
            toast.classList.add('toast-show');
        });

        // Автоудаление
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }

        return toast;
    }

    remove(toast) {
        toast.classList.remove('toast-show');
        toast.classList.add('toast-hide');
        setTimeout(() => toast.remove(), 300);
    }

    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }

    success(message) { this.show(message, 'success'); }
    error(message) { this.show(message, 'error'); }
    warning(message) { this.show(message, 'warning'); }
    info(message) { this.show(message, 'info'); }
}

// ===== ПРОГРЕСС-БАР ЗАГРУЗКИ =====
class UploadProgress {
    constructor(formSelector, options = {}) {
        this.form = document.querySelector(formSelector);
        this.options = {
            progressBarId: 'uploadProgressBar',
            statusTextId: 'uploadStatusText',
            ...options
        };
        this.init();
    }

    init() {
        if (!this.form) return;

        // Создаём элементы прогресс-бара
        this.progressBarContainer = document.createElement('div');
        this.progressBarContainer.className = 'upload-progress-container';
        this.progressBarContainer.innerHTML = `
            <div class="upload-progress-bar">
                <div class="upload-progress-fill" id="${this.options.progressBarId}"></div>
            </div>
            <div class="upload-status-text" id="${this.options.statusTextId}">Ожидание...</div>
        `;
        this.progressBarContainer.style.display = 'none';

        // Вставляем после формы
        this.form.parentNode.insertBefore(this.progressBarContainer, this.form.nextSibling);

        // Отслеживаем отправку формы
        this.form.addEventListener('submit', (e) => this.handleUpload(e));
    }

    handleUpload(e) {
        const fileInput = this.form.querySelector('input[type="file"]');
        if (!fileInput || !fileInput.files[0]) return;

        // Показываем прогресс-бар
        this.progressBarContainer.style.display = 'block';
        this.updateProgress(0, 'Начало загрузки...');

        // Используем XMLHttpRequest для отслеживания прогресса
        const xhr = new XMLHttpRequest();
        const formData = new FormData(this.form);

        xhr.open('POST', this.form.action, true);

        // Получаем CSRF токен
        const csrfToken = this.form.querySelector('[name="csrf_token"]')?.value;
        if (csrfToken) {
            xhr.setRequestHeader('X-CSRFToken', csrfToken);
        }

        // Отслеживаем прогресс
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                this.updateProgress(percent, `Загрузка: ${percent}%`);
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200 || xhr.status === 302) {
                this.updateProgress(100, 'Загрузка завершена!');
                setTimeout(() => {
                    this.progressBarContainer.style.display = 'none';
                    window.location.reload();
                }, 1000);
            } else {
                this.updateProgress(0, 'Ошибка загрузки');
                this.progressBarContainer.classList.add('error');
            }
        });

        xhr.addEventListener('error', () => {
            this.updateProgress(0, 'Ошибка сети');
            this.progressBarContainer.classList.add('error');
        });

        xhr.send(formData);

        // Предотвращаем стандартную отправку
        e.preventDefault();
    }

    updateProgress(percent, text) {
        const fill = document.getElementById(this.options.progressBarId);
        const statusText = document.getElementById(this.options.statusTextId);

        if (fill) {
            fill.style.width = `${percent}%`;
        }
        if (statusText) {
            statusText.textContent = text;
        }
    }
}

// ===== ТЁМНАЯ ТЕМА =====
class DarkMode {
    constructor() {
        this.storageKey = 'darkMode';
        this.button = null;
        this.init();
    }

    init() {
        // Восстанавливаем сохранённую тему
        const isDark = localStorage.getItem(this.storageKey) === 'true';
        this.applyTheme(isDark);

        // Создаём кнопку переключения
        this.createToggleButton();
    }

    applyTheme(isDark) {
        if (isDark) {
            document.documentElement.classList.add('dark-theme');
        } else {
            document.documentElement.classList.remove('dark-theme');
        }
    }

    toggle() {
        const isDark = !document.documentElement.classList.contains('dark-theme');
        this.applyTheme(isDark);
        localStorage.setItem(this.storageKey, isDark.toString());
        this.updateButtonIcon(isDark);
    }

    createToggleButton() {
        this.button = document.createElement('button');
        this.button.className = 'theme-toggle';
        this.button.setAttribute('aria-label', 'Переключить тему');
        this.button.innerHTML = `
            <span class="theme-icon-light">🌙</span>
            <span class="theme-icon-dark">☀️</span>
        `;
        this.button.addEventListener('click', () => this.toggle());

        // Добавляем в навигацию
        const nav = document.querySelector('.nav-glass .flex.items-center.space-x-4');
        if (nav) {
            nav.insertBefore(this.button, nav.firstChild);
        }

        // Обновляем иконку
        this.updateButtonIcon(document.documentElement.classList.contains('dark-theme'));
    }

    updateButtonIcon(isDark) {
        if (this.button) {
            this.button.classList.toggle('active', isDark);
        }
    }
}

// ===== МОБИЛЬНОЕ МЕНЮ =====
class MobileMenu {
    constructor() {
        this.isOpen = false;
        this.init();
    }

    init() {
        // Создаём кнопку hamburger
        this.hamburger = document.createElement('button');
        this.hamburger.className = 'hamburger-menu';
        this.hamburger.setAttribute('aria-label', 'Меню');
        this.hamburger.innerHTML = `
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
        `;

        // Добавляем в навигацию
        const navContainer = document.querySelector('.nav-glass .max-w-5xl');
        const navFlex = document.querySelector('.nav-glass .flex.justify-between');

        if (navFlex) {
            // Вставляем hamburger перед содержимым правой части
            const rightSide = navFlex.querySelector('.flex.items-center.space-x-4');
            if (rightSide) {
                navFlex.insertBefore(this.hamburger, rightSide);
            }
        }

        // Создаём мобильное меню
        this.mobileMenu = document.createElement('div');
        this.mobileMenu.className = 'mobile-menu';
        this.mobileMenu.innerHTML = this.getMenuContent();

        document.body.appendChild(this.mobileMenu);

        // Обработчики
        this.hamburger.addEventListener('click', () => this.toggle());

        // Закрытие при клике вне меню
        document.addEventListener('click', (e) => {
            if (this.isOpen &&
                !this.mobileMenu.contains(e.target) &&
                !this.hamburger.contains(e.target)) {
                this.close();
            }
        });

        // Закрытие при изменении размера
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768 && this.isOpen) {
                this.close();
            }
        });
    }

    getMenuContent() {
        const isAdmin = document.body.querySelector('[data-is-admin]')?.dataset.isAdmin === 'true';

        return `
            <div class="mobile-menu-content">
                <div class="mobile-menu-header">
                    <span class="text-xl font-bold">Сайт Макса</span>
                    <button class="mobile-menu-close" onclick="mobileMenu.close()">✕</button>
                </div>
                <nav class="mobile-menu-nav">
                    <a href="/" class="mobile-menu-item">
                        <span>🏠</span> Главная
                    </a>
                    ${isAdmin ? `
                    <a href="/create" class="mobile-menu-item">
                        <span>📝</span> Создать пост
                    </a>
                    <a href="/logout" class="mobile-menu-item">
                        <span>🚪</span> Выйти
                    </a>
                    ` : `
                    <a href="/login" class="mobile-menu-item">
                        <span>🔐</span> Вход
                    </a>
                    `}
                </nav>
            </div>
        `;
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.hamburger.classList.add('active');
        this.mobileMenu.classList.add('mobile-menu-open');
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.isOpen = false;
        this.hamburger.classList.remove('active');
        this.mobileMenu.classList.remove('mobile-menu-open');
        document.body.style.overflow = '';
    }
}

// ===== ИНИЦИАЛИЗАЦИЯ =====
let toast;
let mobileMenu;
let darkMode;
let uploadProgress;

document.addEventListener('DOMContentLoaded', () => {
    // Инициализация компонентов
    toast = new ToastManager();
    mobileMenu = new MobileMenu();
    darkMode = new DarkMode();
    uploadProgress = new UploadProgress('form[method="POST"][enctype="multipart/form-data"]');

    // Показываем flash-сообщения как toast
    const flashMessages = document.querySelectorAll('.alert-success, .alert-error');
    flashMessages.forEach((msg, index) => {
        const type = msg.classList.contains('alert-error') ? 'error' : 'success';
        setTimeout(() => {
            toast.show(msg.textContent.trim(), type);
            // Скрываем оригинальное сообщение
            msg.style.display = 'none';
        }, index * 200);
    });

    // HTMX события для toast
    document.body.addEventListener('htmx:afterRequest', (event) => {
        if (event.detail.successful) {
            toast.success('Операция выполнена успешно');
        } else if (event.detail.failed) {
            toast.error('Ошибка при выполнении операции');
        }
    });
});

// Экспорт для глобального доступа
window.toast = toast;
window.mobileMenu = mobileMenu;
