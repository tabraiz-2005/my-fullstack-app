// Wait for the DOM to be fully loaded
window.addEventListener("DOMContentLoaded", () => {

  // --- DOM Elements ---
  const chatMessagesDiv = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const userInputElem = document.getElementById("user-input");
  const submitBtn = document.getElementById("submitBtn");
  const welcomeMessage = document.getElementById("welcome-message");

  // --- State ---
  let messages = []; // This will hold the chat history for the API
  let autoScrollState = true;

  // --- Markdown Renderer ---
  const md = window.markdownit ? window.markdownit() : { render: (text) => text };

  // --- Helper Functions ---

  /**
   * Renders message content to an element, handling markdown and code highlighting.
   */
  function renderMessageContent(content, element) {
    let renderedContent = md.render(content).trim();
    element.innerHTML = renderedContent;
    if (window.hljs) {
      element.querySelectorAll("pre code").forEach(window.hljs.highlightElement);
    }
  }

  /**
   * Adds a message to the chat display.
   */
  function addMessageToDiv(role, content = "") {
    // Hide welcome message on first chat
    if (welcomeMessage) {
      welcomeMessage.style.display = "none";
    }

    let messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}-message`;

    let messageText = document.createElement("p");
    messageDiv.appendChild(messageText);

    if (content) {
      renderMessageContent(content, messageText);
    }

    chatMessagesDiv.appendChild(messageDiv);
    autoScroll();
    return messageText; // Return the <p> tag for streaming
  }

  /**
   * Adds or removes a typing indicator.
   */
  function showTypingIndicator(show) {
    let indicator = document.getElementById("typing-indicator");
    if (show) {
      if (!indicator) {
        let messageDiv = document.createElement("div");
        messageDiv.className = "message assistant-message";
        messageDiv.id = "typing-indicator";
        messageDiv.innerHTML = "<p class='typing-indicator'><span></span><span></span><span></span></p>";
        chatMessagesDiv.appendChild(messageDiv);
        autoScroll();
      }
    } else {
      if (indicator) {
        indicator.remove();
      }
    }
  }

  /**
   * Handles the streaming response from the backend.
   */
  async function handleResponse(response, messageTextElem) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let assistantMessage = "";
    let firstChunk = true;

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        messages.push({ role: "assistant", content: assistantMessage });
        break;
      }

      if (firstChunk) {
        showTypingIndicator(false); // Remove indicator
        firstChunk = false;
      }

      const text = decoder.decode(value);
      assistantMessage += text;

      renderMessageContent(assistantMessage, messageTextElem);
      autoScroll();
    }
  }

  /**
   * Sends the chat history to the backend.
   */
  async function postRequest() {
    try {
      const response = await fetch("/gpt4", {
        method: "POST",
        body: JSON.stringify({ messages }),
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }
      return response;

    } catch (error) {
      console.error("Fetch error:", error);
      showTypingIndicator(false);
      addMessageToDiv("assistant", `**Error:** Unable to connect. ${error.message}`);
      return null;
    }
  }

  /**
   * Scrolls the chat window to the bottom if auto-scroll is enabled.
   */
  function autoScroll() {
    if (autoScrollState) {
      chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
    }
  }

  /**
   * Updates the send button's disabled state.
   */
  function updateButtonState() {
    submitBtn.disabled = userInputElem.value.trim() === "";
  }

  // --- Event Listeners ---

  // Handle form submission
  chatForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    let userInput = userInputElem.value.trim();
    if (userInput === "") return;

    submitBtn.disabled = true;

    messages.push({ role: "user", content: userInput });
    addMessageToDiv("user", userInput);
    
    userInputElem.value = "";
    userInputElem.style.height = "auto"; // Reset height

    showTypingIndicator(true);

    const response = await postRequest();
    if (response) {
      const assistantMessageElem = addMessageToDiv("assistant");
      await handleResponse(response, assistantMessageElem);
    }

    submitBtn.disabled = false;
    userInputElem.focus();
  });

  // Auto-resize textarea
  userInputElem.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
    updateButtonState();
  });

  // Check button state
  userInputElem.addEventListener("keyup", updateButtonState);

  // Handle Enter key (Shift+Enter for new line)
  userInputElem.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit();
    }
  });

  // Control auto-scroll
  chatMessagesDiv.addEventListener("scroll", function () {
    const isAtBottom =
      chatMessagesDiv.scrollHeight - chatMessagesDiv.clientHeight <=
      chatMessagesDiv.scrollTop + 10;
    autoScrollState = isAtBottom;
  });

  // --- Initial Setup ---
  updateButtonState();
  userInputElem.focus();
});
