document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("upload-form");
    const loadingMessage = document.getElementById("loading-message");
    const dotAnimation = document.getElementById("dot-animation");
    let dots = 0;

    // Show loading message but keep form visible on submit
    form.addEventListener("submit", function(event) {
        loadingMessage.classList.remove("hidden");  // Show the loading message

        // Animate the dots after "Working"
        setInterval(function() {
            dots = (dots + 1) % 4;
            dotAnimation.innerHTML = ".".repeat(dots);  // Add 1 to 3 dots in a repeating loop
        }, 500);  // 500ms interval for the dot animation
    });
});
