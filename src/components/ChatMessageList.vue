
<template>
  <div class="message-list">
    <div
      v-for="(m,i) in messages"
      :key="i"
      :class="['message', m.role]"
    >
      <div class="bubble">{{ m.text }}</div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
export default {
  name: 'ChatMessageList',
  props: {
    messages: { type: Array, required: true }
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
  margin: 4px 0;
  display: flex;
}
.message.user     { justify-content: flex-end; }
.message.assistant{ justify-content: flex-start; }
.bubble {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 12px;
  line-height: 1.4;
}
.message.user .bubble {
  background: #135388;
  color: white;
}
.message.assistant .bubble {
  background: #e1e8f0;
  color: #333;
}
</style>
