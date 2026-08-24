document.addEventListener('DOMContentLoaded', function() {
    const burger = document.getElementById('burgerBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    if (burger && mobileMenu) {
        burger.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
        });
    }
});