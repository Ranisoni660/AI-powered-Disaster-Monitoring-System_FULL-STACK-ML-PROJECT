(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();
    
    
    // Initiate the wowjs
    new WOW().init();


    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 45) {
            $('.nav-bar').addClass('sticky-top');
        } else {
            $('.nav-bar').removeClass('sticky-top');
        }
    });
    
    
    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });


    // Header carousel
    $(".header-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        items: 1,
        dots: true,
        loop: true,
        nav : true,
        navText : [
            '<i class="bi bi-chevron-left"></i>',
            '<i class="bi bi-chevron-right"></i>'
        ]
    });


    // Testimonials carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        margin: 24,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ],
        responsive: {
            0:{
                items:1
            },
            992:{
                items:2
            }
        }
    });
    

    document.addEventListener('DOMContentLoaded', function() {
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        
        // Check for saved theme preference or use device preference
        const savedTheme = localStorage.getItem('theme') || 
                          (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                          
        // Apply saved theme on page load
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateIcon(savedTheme);
        
        // Toggle theme on button click
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            // Change the theme
            document.documentElement.setAttribute('data-theme', newTheme);
            
            // Save theme preference
            localStorage.setItem('theme', newTheme);
            
            // Update button icon
            updateIcon(newTheme);
        });
        
        // Helper function to update the icon based on theme
        function updateIcon(theme) {
            if (theme === 'dark') {
                themeIcon.classList.remove('bi-brightness-high');
                themeIcon.classList.add('bi-moon');
            } else {
                themeIcon.classList.remove('bi-moon');
                themeIcon.classList.add('bi-brightness-high');
            }
        }
    });

    document.addEventListener('DOMContentLoaded', () => {
            const disasterWord = document.querySelector('.disaster-word');
            const animateDisaster = () => {
                if (disasterWord) {
                    const text = disasterWord.textContent;
                    disasterWord.innerHTML = text.split('').map(char => `<span>${char}</span>`).join('');
                }
            };
            animateDisaster();
            setInterval(animateDisaster, 3000);
        });
})(jQuery);

