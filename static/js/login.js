document.addEventListener("DOMContentLoaded", function () {
    const password = document.getElementById("password");
    const toggle = document.getElementById("togglePassword");

    if (password && toggle) {
        toggle.addEventListener("click", function () {
            const showing = password.type === "password";
            password.type = showing ? "text" : "password";
            toggle.textContent = showing ? "◎" : "◉";
            toggle.setAttribute("aria-label", showing ? "Ẩn mật khẩu" : "Hiện mật khẩu");
        });
    }
});
