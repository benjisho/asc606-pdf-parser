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
window.tailwind.config = {
    darkMode: ['class'],
    theme: {
        extend: {
            colors: {
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
            },
        }
    }
}
// Toggle AI Summary Switch
const aiSummaryToggle = document.getElementById('ai-summary-toggle');
const aiSummaryInput = document.getElementById('ai_summary');
aiSummaryToggle.addEventListener('change', () => {
    const isEnabled = aiSummaryToggle.checked;
    aiSummaryInput.value = isEnabled ? 'true' : 'false';
    const toggleLabel = aiSummaryToggle.nextElementSibling;
    toggleLabel.firstElementChild.classList.toggle('bg-[#74AA9C]', isEnabled); // Green when enabled
    toggleLabel.firstElementChild.classList.toggle('bg-red-500', !isEnabled); // Red when disabled
    toggleLabel.lastElementChild.classList.toggle('translate-x-6', isEnabled);
});