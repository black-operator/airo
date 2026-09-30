(() => {
  const chat = document.querySelector("[data-chat]");
  if (!chat) return;
  const conversationId = chat.dataset.conversationId;
  const form = chat.querySelector("[data-composer]");
  const input = chat.querySelector("[data-composer-input]");
  const list = chat.querySelector("[data-message-list]");
  const scroller = chat.querySelector("[data-message-scroll]");
  const sendButton = chat.querySelector("[data-send]");
  const stopButton = chat.querySelector("[data-stop]");
  const errorBox = chat.querySelector("[data-generation-error]");
  const state = chat.querySelector("[data-model-state]");
  const detailsPanel = chat.querySelector("[data-details-panel]");
  const detailsButtons = [...document.querySelectorAll("[data-details-toggle]")];
  const desktopDetails = window.matchMedia("(min-width: 1051px)");
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  let controller = null;

  const scrollToBottom = (smooth = false) => {
    scroller.scrollTo({ top: scroller.scrollHeight, behavior: smooth ? "smooth" : "auto" });
  };
  const resize = () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
  };
  const messageElement = (role, text = "") => {
    const article = document.createElement("article");
    article.className = `message message--${role}`;
    const label = document.createElement("div");
    label.className = "message__label";
    label.textContent = role === "user" ? "Du" : document.querySelector(".chat-header__identity strong").textContent;
    const content = document.createElement("div");
    content.className = "message__content";
    content.textContent = text;
    article.append(label, content);
    list.append(article);
    return { article, content };
  };

  const renderSimpleMarkdown = (element) => {
    const escaped = element.textContent
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
    element.innerHTML = escaped
      .replace(/\*\*([^*\n]+)\*\*/g, "<em>$1</em>")
      .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
      .replaceAll("\n", "<br>");
  };

  const setGenerating = (active) => {
    input.disabled = active;
    sendButton.hidden = active;
    stopButton.hidden = !active;
    chat.classList.toggle("is-generating", active);
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || controller) return;
    errorBox.hidden = true;
    messageElement("user", text);
    input.value = "";
    resize();
    const assistant = messageElement("assistant");
    assistant.article.classList.add("is-streaming");
    setGenerating(true);
    scrollToBottom(true);
    controller = new AbortController();
    try {
      const response = await fetch(`/api/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ content: text }),
        signal: controller.signal,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || `Fehler ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line) continue;
          const packet = JSON.parse(line);
          if (packet.type === "token") assistant.content.textContent += packet.content;
          if (packet.type === "error") throw new Error(packet.message);
        }
        scrollToBottom();
        if (done) break;
      }
    } catch (error) {
      if (error.name === "AbortError") {
        assistant.article.classList.add("is-interrupted");
      } else {
        assistant.article.remove();
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      }
    } finally {
      assistant.article.classList.remove("is-streaming");
      if (assistant.content.textContent) renderSimpleMarkdown(assistant.content);
      controller = null;
      setGenerating(false);
      input.focus();
    }
  });

  stopButton.addEventListener("click", () => controller?.abort());
  input.addEventListener("input", resize);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  const setDetailsState = (open) => {
    if (desktopDetails.matches) {
      chat.classList.toggle("details-collapsed", !open);
      detailsPanel.classList.remove("is-open");
    } else {
      detailsPanel.classList.toggle("is-open", open);
      chat.classList.remove("details-collapsed");
    }
    detailsButtons.forEach((button) => button.setAttribute("aria-expanded", String(open)));
  };
  detailsButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const open = desktopDetails.matches
        ? chat.classList.contains("details-collapsed")
        : !detailsPanel.classList.contains("is-open");
      setDetailsState(open);
    });
  });
  desktopDetails.addEventListener("change", () => setDetailsState(desktopDetails.matches));

  fetch("/api/ollama/status")
    .then((response) => response.json())
    .then((data) => {
      state.className = data.online && data.model_ready ? "is-online" : "is-offline";
      state.innerHTML = `<i></i>${data.online ? (data.model_ready ? data.model : "Modell fehlt") : "Ollama offline"}`;
    })
    .catch(() => { state.textContent = "Status unbekannt"; });
  resize();
  scrollToBottom();
})();
