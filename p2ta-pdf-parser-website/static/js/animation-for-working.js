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
  // Example JavaScript to handle form submission and display messages
  document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();
    document.getElementById('loading-message').classList.remove('hidden');
    // Simulate form submission and response
    setTimeout(() => {
      document.getElementById('loading-message').classList.add('hidden');
      document.getElementById('success-message').classList.remove('hidden');
      document.getElementById('success-message').textContent = 'Upload successful!';
      document.getElementById('output-file-message').classList.remove('hidden');
      document.getElementById('download-link').href = '/download/sample.txt';
    }, 2000);
  });
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