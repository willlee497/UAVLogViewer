<template>
  <div class="message-list">
    <!-- Default welcome message when no messages exist -->
    <div v-if="messages.length === 0" class="message assistant welcome">
      <div class="bubble">
        <div class="welcome-content">
          <h3>🤖 Flight Analysis Assistant</h3>
          <p>Ask me anything about your flight data!</p>
          <div class="suggestions">
            <span
              class="suggestion"
              @click="$emit('send-question', 'What anomalies occurred?')">
              What anomalies occurred?
            </span>
            <span
              class="suggestion"
              @click="$emit('send-question', 'How was the GPS performance?')">
              How was the GPS performance?
            </span>
            <span
              class="suggestion"
              @click="$emit('send-question', 'Analyze the battery consumption')">
              Analyze the battery consumption
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Existing messages -->
    <div
      v-for="(m,i) in messages"
      :key="i"
      :class="['message', m.role]"
    >
      <div class="bubble">
        <!-- Render markdown for assistant messages, plain text for user -->
        <div v-if="m.role === 'assistant'" v-html="formatMarkdown(m.text)"></div>
        <div v-else>{{ m.text }}</div>
      </div>
    </div>

    <!-- Loading bubbles when processing -->
    <div v-if="loading" class="message assistant">
      <div class="bubble loading-bubble">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
export default {
  name: 'ChatMessageList',
  props: {
    messages: { type: Array, required: true },
    loading: { type: Boolean, default: false }
  },
  methods: {
    formatMarkdown(text) {
      // Enhanced markdown-to-HTML conversion for chat responses
      let html = text;
      
      // First, handle headers BEFORE line breaks (so ^ anchor works properly)
      html = html.replace(/^### (.*)$/gim, '<h4>$1</h4>');
      html = html.replace(/^## (.*)$/gim, '<h3>$1</h3>');
      html = html.replace(/^# (.*)$/gim, '<h2>$1</h2>');
      
      // Handle bold text (before line breaks to catch multi-line bold)
      html = html.replace(/\*\*(.*?)\*\*/gs, '<strong>$1</strong>');
      
      
            // Checkboxes (keep these for recommendations)
      html = html.replace(/^- \[ \] (.*)$/gim, '<li class="checkbox">☐ $1</li>');
      html = html.replace(/^- \[x\] (.*)$/gim, '<li class="checkbox checked">☑ $1</li>');
      
      // Handle line breaks
      html = html.replace(/\n/g, '<br>');
      
      // Wrap consecutive list items in <ul> tags
      html = html.replace(/(<li[^>]*>.*?<\/li>(<br>)?)+/gs, function(match) {
        // Remove <br> tags between list items and wrap in <ul>
        const cleanList = match.replace(/<br>/g, '');
        return '<ul>' + cleanList + '</ul>';
      });
      
      // Clean up extra line breaks around lists and headers
      html = html.replace(/<br><ul>/g, '<br><ul>');
      html = html.replace(/<\/ul><br>/g, '</ul><br>');
      html = html.replace(/<br><h([1-4])>/g, '<br><h$1>');
      html = html.replace(/<\/h([1-4])><br>/g, '</h$1><br>');
      
      // Add some spacing around headers for better visual separation
      html = html.replace(/<h([1-4])>/g, '<br><h$1>');
      html = html.replace(/<\/h([1-4])>/g, '</h$1><br>');
      
      // Clean up multiple consecutive <br> tags
      html = html.replace(/(<br>){3,}/g, '<br><br>');
      html = html.replace(/^<br>/, ''); // Remove leading <br>
      
      return html;
    }
  }
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  background: #f5f7fa;
}
.message {
  margin: 8px 0;
  display: flex;
}
.message.user     { justify-content: flex-end; }
.message.assistant{ justify-content: flex-start; }
.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.5;
  word-wrap: break-word;
}
.message.user .bubble {
  background: #135388;
  color: white;
}
.message.assistant .bubble {
  background: #e1e8f0;
  color: #333;
}

/* Welcome message styling */
.message.welcome .bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  max-width: 85%;
}
.welcome-content h3 {
  margin: 0 0 8px 0;
  font-size: 1.2em;
}
.welcome-content p {
  margin: 0 0 12px 0;
  opacity: 0.9;
}
.suggestions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.suggestion {
  background: rgba(255,255,255,0.2);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.9em;
  cursor: pointer;
  transition: background 0.2s;
}
.suggestion:hover {
  background: rgba(255,255,255,0.3);
}

/* Loading animation */
.loading-bubble {
  background: #e1e8f0;
  min-width: 60px;
}
.loading-dots {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
}
.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
  animation: bounce 1.4s infinite ease-in-out both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
.loading-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* Markdown styling */
.bubble h2, .bubble h3, .bubble h4 {
  margin: 12px 0 8px 0;
  color: #2c3e50;
}
.bubble h2 { font-size: 1.3em; border-bottom: 2px solid #3498db; padding-bottom: 4px; }
.bubble h3 { font-size: 1.2em; color: #e67e22; }
.bubble h4 { font-size: 1.1em; color: #8e44ad; }
.bubble ul {
  margin: 8px 0;
  padding-left: 20px;
}
.bubble li {
  margin: 4px 0;
}
.bubble li.checkbox {
  list-style: none;
  margin-left: -20px;
}
.bubble li.checkbox.checked {
  color: #27ae60;
}
.bubble strong {
  color: #2c3e50;
}
</style>
