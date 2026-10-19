
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("chatbot-toggle");
  const panel = document.getElementById("chatbot-panel");
  const close = document.getElementById("chatbot-close");
  const form = document.getElementById("chatbot-form");
  const input = document.getElementById("chatbot-input");
  const messages = document.getElementById("chatbot-messages");

  if (!toggle || !panel || !close || !form || !input || !messages) {
    console.error("Chatbot HTML elements are missing.");
    return;
  }

  toggle.addEventListener("click", () => {
   panel.classList.remove("hidden");
panel.style.display = "flex";
  });

  close.addEventListener("click", () => {
    panel.classList.add("hidden");
  });

  function addMessage(text, type) {
    const message = document.createElement("div");
    message.className = type === "user" ? "user-message" : "bot-message";
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
    return message;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";

    const waiting = addMessage("Thinking...", "bot");

    try {
      const response = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.reply || "Chatbot service error.");
      }

      waiting.textContent = data.reply || "Please try again.";
    } catch (error) {
      waiting.textContent =
        "Reply nahi mila. Chatbot backend ya connection check karna hoga.";
      console.error("Chatbot error:", error);
    }
  });
});
