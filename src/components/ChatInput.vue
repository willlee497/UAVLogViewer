<!-- eslint-disable -->
<template>
  <div class="chat-input">
    <input
      v-model="text"
      @keyup.enter="send"
      :disabled="loading || disabled"
      :placeholder="placeholder"
      autofocus
    >
    <button
      @click="send"
      :disabled="loading || disabled || !text"
    >
      {{ loading ? '…' : 'Send' }}
    </button>
  </div>
</template>

<script>
/* eslint-disable */
export default {
  name: 'ChatInput',
  props: {
    loading:  Boolean,   // spinner flag
    disabled: Boolean,    // parent decides if we can type
    placeholder: String,
  },
  data () {
    return { text: '' }
  },
  methods: {
    send () {
      const msg = this.text.trim()
      if (!msg) return
      this.$emit('send', msg)   // hand the message to parent
      this.text = ''            // clear the box
    }
  }
}
</script>

<style scoped>
.chat-input { display:flex; padding-top:8px; }
.chat-input input {
  flex:1;
  padding:6px 8px;
  border:1px solid #ccc;
  border-radius:4px;
}
.chat-input button {
  margin-left:8px;
  padding:6px 16px;
  background:#135388;
  color:#fff;
  border:none;
  border-radius:4px;
  cursor:pointer;
}
.chat-input button:disabled {
  background:#999;
  cursor:default;
  min-height:38px;
}
</style>
