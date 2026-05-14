// Рекламный слайдер на чистом JavaScript
class BannerSlider {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.slides = [];
        this.currentSlide = 0;
        this.interval = null;
        this.autoPlay = options.autoPlay !== false;
        this.intervalTime = options.intervalTime || 5000;
        this.init();
    }

    init() {
        if (!this.container) return;

        // Получаем все слайды
        this.slides = Array.from(this.container.querySelectorAll('.slider-slide'));
        if (this.slides.length === 0) return;

        // Создаем элементы управления
        this.createIndicators();
        this.createControls();

        // Показываем первый слайд
        this.showSlide(0);

        // Запускаем автопрокрутку
        if (this.autoPlay && this.slides.length > 1) {
            this.startAutoPlay();
        }

        // Добавляем обработчики событий
        this.addEventListeners();
    }

    createIndicators() {
        const indicators = document.createElement('div');
        indicators.className = 'slider-indicators';

        this.slides.forEach((_, index) => {
            const dot = document.createElement('div');
            dot.className = 'slider-dot';
            dot.dataset.index = index;
            dot.addEventListener('click', () => this.showSlide(index));
            indicators.appendChild(dot);
        });

        this.container.appendChild(indicators);
        this.indicators = indicators;
    }

    createControls() {
        const prevBtn = document.createElement('button');
        prevBtn.className = 'slider-control slider-prev';
        prevBtn.innerHTML = '❮';
        prevBtn.addEventListener('click', () => this.prevSlide());

        const nextBtn = document.createElement('button');
        nextBtn.className = 'slider-control slider-next';
        nextBtn.innerHTML = '❯';
        nextBtn.addEventListener('click', () => this.nextSlide());

        this.container.appendChild(prevBtn);
        this.container.appendChild(nextBtn);

        // Пауза при наведении
        this.container.addEventListener('mouseenter', () => this.pauseAutoPlay());
        this.container.addEventListener('mouseleave', () => this.resumeAutoPlay());
    }

    showSlide(index) {
        if (index < 0) index = this.slides.length - 1;
        if (index >= this.slides.length) index = 0;

        // Скрываем все слайды
        this.slides.forEach(slide => {
            slide.classList.remove('active');
        });

        // Показываем текущий слайд
        this.slides[index].classList.add('active');
        this.currentSlide = index;

        // Обновляем индикаторы
        if (this.indicators) {
            const dots = this.indicators.querySelectorAll('.slider-dot');
            dots.forEach((dot, i) => {
                if (i === index) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
        }
    }

    nextSlide() {
        this.showSlide(this.currentSlide + 1);
        this.resetAutoPlay();
    }

    prevSlide() {
        this.showSlide(this.currentSlide - 1);
        this.resetAutoPlay();
    }

    startAutoPlay() {
        if (this.interval) clearInterval(this.interval);
        this.interval = setInterval(() => this.nextSlide(), this.intervalTime);
    }

    pauseAutoPlay() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    resumeAutoPlay() {
        if (this.autoPlay && !this.interval && this.slides.length > 1) {
            this.startAutoPlay();
        }
    }

    resetAutoPlay() {
        if (this.autoPlay) {
            this.pauseAutoPlay();
            this.startAutoPlay();
        }
    }

    addEventListeners() {
        // Клавиатурная навигация
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.prevSlide();
                this.resetAutoPlay();
            } else if (e.key === 'ArrowRight') {
                this.nextSlide();
                this.resetAutoPlay();
            }
        });

        // Поддержка touch для мобильных
        let touchStartX = 0;
        let touchEndX = 0;

        this.container.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });

        this.container.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            if (touchEndX < touchStartX - 50) {
                this.nextSlide();
                this.resetAutoPlay();
            } else if (touchEndX > touchStartX + 50) {
                this.prevSlide();
                this.resetAutoPlay();
            }
        });
    }
}

// Инициализация слайдера после загрузки страницы
document.addEventListener('DOMContentLoaded', function() {
    const sliderContainer = document.getElementById('mainSlider');
    if (sliderContainer) {
        new BannerSlider('mainSlider', {
            autoPlay: true,
            intervalTime: 5000
        });
    }
});