document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatbox = document.getElementById("chatbox");
  
    chatForm.addEventListener("submit", async function (event) {
      event.preventDefault();
  
      const userMessage = chatInput.value.trim();
      if (!userMessage) return;
  
      // Display the user's message
      const userMessageElement = document.createElement("div");
      userMessageElement.className = "text-right mb-2";
      userMessageElement.textContent = userMessage;
      chatbox.appendChild(userMessageElement);
  
      // Clear the input field
      chatInput.value = "";
  
      // Scroll chatbox to the bottom
      chatbox.scrollTop = chatbox.scrollHeight;
  
      // Send user message to the backend
      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: userMessage }),
        });
  
        if (!response.ok) throw new Error("Failed to fetch response from server.");
  
        const data = await response.json();
  
        // Display the chatbot's response
        const botMessageElement = document.createElement("div");
        botMessageElement.className = "text-left mb-2 text-muted-foreground";
        botMessageElement.textContent = data.response;
        chatbox.appendChild(botMessageElement);
  
        // Scroll chatbox to the bottom
        chatbox.scrollTop = chatbox.scrollHeight;
      } catch (error) {
        console.error(error);
        const errorMessageElement = document.createElement("div");
        errorMessageElement.className = "text-left mb-2 text-destructive";
        errorMessageElement.textContent = "Error: Could not get a response from the chatbot.";
        chatbox.appendChild(errorMessageElement);
      }
    });
  });