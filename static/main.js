// Wait for the DOM to be fully loaded before running scripts
window.addEventListener("DOMContentLoaded", () => {

  // --- DOM Elements ---
  const chatMessagesDiv = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const userInputElem = document.getElementById("user-input");
  const submitBtn = document.getElementById("submitBtn");
  const menuToggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  
  // --- NEW: Image Upload Elements ---
  const uploadBtn = document.getElementById("upload-btn");
  const imageUploadInput = document.getElementById("image-upload-input");
  const imagePreviewContainer = document.getElementById("image-preview-container");

  // --- State ---
  let messages = [];
  let autoScrollState = true;
  let currentImageBase64 = null; // --- NEW: To store image data ---

  // --- Markdown Renderer ---
  const md = window.markdownit ? window.markdownit() : { render: (text) => text };

  // --- Helper Functions ---

  /**
   * Renders and highlights code in a message element.
   * @param {string} content The message content.
   * @param {HTMLElement} element The <p> tag to put the content in.
   */
  function renderMessageContent(content, element) {
    let renderedContent = md.render(content).trim();
    element.innerHTML = renderedContent;

    if (window.hljs) {
      element.querySelectorAll("pre code").forEach((codeElement) => {
        window.hljs.highlightElement(codeElement);
      });
    }
  }

  /**
   * Adds a message to the chat display.
   * @param {string} role 'user' or 'assistant'.
   * @param {string} [content] The message content.
   * @returns {HTMLElement} The <p> element where content will be streamed.
   */
  function addMessageToDiv(role, content = "") {
    let messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}-message`;

    let messageText = document.createElement("p");
    messageDiv.appendChild(messageText);

    if (content) {
      renderMessageContent(content, messageText);
    }

    chatMessagesDiv.appendChild(messageDiv);
    autoScroll();

    return messageText;
  }

  /**
   * Adds or removes a typing indicator.
   * @param {boolean} show True to show, false to remove.
   */
  function showTypingIndicator(show) {
    let indicator = document.getElementById("typing-indicator");
    if (show) {
      if (!indicator) {
        indicator = document.createElement("div");
        indicator.id = "typing-indicator";
        indicator.className = "message assistant-message typing-indicator";
        indicator.innerHTML = "<span></span><span></span><span></span>";
        chatMessagesDiv.appendChild(indicator);
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
   * @param {Response} response The fetch response object.
   * @param {HTMLElement} messageTextElem The target <p> element.
   */
  async function handleResponse(response, messageTextElem) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let assistantMessage = "";
    let firstChunk = true;

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        messages.push({
          role: "assistant",
          content: assistantMessage,
        });
        break;
      }

      if (firstChunk) {
        showTypingIndicator(false); // Remove indicator on first text
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
   * @param {string | null} imageBase64 The base64 encoded image string
   * @returns {Promise<Response | null>} The fetch promise or null on error.
   */
  async function postRequest(imageBase64 = null) {
    try {
      // Get the last user message text
      const lastUserMessage = messages.length > 0 ? messages[messages.length - 1].content : "";
      
      const payload = {
          messages: messages,
          image: imageBase64,
      };

      const response = await fetch("/gpt4", {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }
      
      return response;

    } catch (error) {
      console.error("Fetch error:", error);
      showTypingIndicator(false);
      addMessageToDiv("assistant", `**Error:** Unable to connect to the server. ${error.message}`);
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
    // Enable button if there is text OR an image
    const hasText = userInputElem.value.trim() !== "";
    const hasImage = currentImageBase64 !== null;
    submitBtn.disabled = !hasText && !hasImage;
  }
  
  // --- NEW: Function to remove image preview ---
  function removeImagePreview() {
    currentImageBase64 = null;
    imageUploadInput.value = null; // Reset file input
    imagePreviewContainer.innerHTML = "";
    imagePreviewContainer.style.display = "none";
    updateButtonState(); // Check if button should be disabled
  }

  // --- Event Listeners ---

  // Handle form submission
  chatForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    let userInput = userInputElem.value.trim();
    
    // Check if there is text or an image
    if (userInput === "" && !currentImageBase64) {
      return;
    }

    // Disable button during response
    submitBtn.disabled = true;

    // Get the image and clear it
    const imageToSend = currentImageBase64;
    if (imageToSend) {
        // Add the image to the user's message in the UI
        const img = document.createElement("img");
        img.src = imageToSend;
        img.className = "message-image"; // You can style this
        addMessageToDiv("user", userInput).appendChild(img);
        removeImagePreview();
    } else {
        addMessageToDiv("user", userInput);
    }

    // Add user message to state
    messages.push({ role: "user", content: userInput });
    
    // Clear input and reset height
    userInputElem.value = "";
    userInputElem.style.height = "auto";

    // Show typing indicator
    showTypingIndicator(true);

    // Post request and handle stream
    const response = await postRequest(imageToSend); // <-- Pass image
    if (response) {
      const assistantMessageElem = addMessageToDiv("assistant");
      await handleResponse(response, assistantMessageElem);
    }

    // Re-enable button
    updateButtonState(); // Use function to check state
    userInputElem.focus();
  });

  // Auto-resize textarea
  userInputElem.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
    updateButtonState();
  });

  // Check button state on key up (for paste, etc.)
  userInputElem.addEventListener("keyup", updateButtonState);

  // Handle Enter key for submission (Shift+Enter for new line)
  userInputElem.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit(); // Triggers the 'submit' event
    }
  });

  // Control auto-scroll
  chatMessagesDiv.addEventListener("scroll", function () {
    const isAtBottom =
      chatMessagesDiv.scrollHeight - chatMessagesDiv.clientHeight <=
      chatMessagesDiv.scrollTop + 10; // 10px buffer
    autoScrollState = isAtBottom;
  });

  // Mobile menu toggle
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("is-open");
  });
  
  // --- NEW: Event Listeners for Images ---
  uploadBtn.addEventListener("click", () => {
    imageUploadInput.click();
  });

  imageUploadInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Check file size (e.g., max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert("Image is too large (max 5MB).");
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      currentImageBase64 = e.target.result;
      
      // Show preview
      imagePreviewContainer.innerHTML = ""; // Clear old preview
      const img = document.createElement("img");
      img.src = currentImageBase64;
      img.className = "image-preview";
      
      const removeBtn = document.createElement("button");
      removeBtn.id = "remove-image-btn";
      removeBtn.type = "button"; // Don't submit form
      removeBtn.innerHTML = "&times;";
      removeBtn.onclick = removeImagePreview; // Hook up remove logic
      
      imagePreviewContainer.appendChild(img);
      imagePreviewContainer.appendChild(removeBtn);
      imagePreviewContainer.style.display = "block";
      
      updateButtonState(); // Enable send button
    };
    reader.readAsDataURL(file);
  });
  // --- END NEW ---

  // --- Initial Setup ---
  updateButtonState(); // Set initial button state (disabled)
  userInputElem.focus(); // Focus input on page load
});

