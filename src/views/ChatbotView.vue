<!-- eslint-disable -->
<template>
  <div class="chatbot-view">
    <!-- top bar -->
    <div class="chat-header">
      <button class="back-button" @click="goBack">← Back</button>
      <h2>Flight Q&amp;A</h2>
    </div>

    <!-- conversation -->
    <ChatMessageList :messages="messages" :loading="loading" @send-question="onSend" class="scroll-area"/>

    <!-- composer -->
    <ChatInput class="composer"
               @send="onSend"
               :loading="loading"
               :disabled="!sessionReady"
               placeholder="Ask about this flight…"
               />
  </div>
</template>

<script>
/* eslint-disable */
import axios            from 'axios'
import ChatMessageList  from '@/components/ChatMessageList.vue'
import ChatInput        from '@/components/ChatInput.vue'
import { store }        from '@/components/Globals.js'

export default {
  name: 'ChatbotView',
  components: { ChatMessageList, ChatInput },

  data () {
    return {
      messages: store.chatHistory,         // { role: 'user'|'assistant', text }
      loading : false
    }
  },

  computed: {
    // convenience flag used to disable the ChatInput
    sessionReady () {
      console.log('🔑 currentSessionId =', store.currentSessionId);
      return !!store.currentSessionId
    }
  },

  methods: {
    goBack () {
      this.$router.back()
    },

    async onSend (text) {
      if (!text) return               // nothing typed
      if (!this.sessionReady) {
        // shouldn't happen – ChatInput is disabled – but belt & suspenders
        return alert('⚠️  Please upload a .bin log before asking questions.')
      }
      //store.chatHistory.push({ role:'user', text })
      //store.chatHistory.push({ role:'assistant', text: resp.data.answer })
      store.chatHistory.push({ role:'user', text })
      this.loading = true

      
      console.log('📤 payload:', { flight_id: store.currentSessionId, question: text })

      try {
        /* ---------- API CALL ---------- */
        const resp = await axios.post('/api/chat', {
          flight_id: store.currentSessionId,
          question : text
        })
        /* -------------------------------- */

        // display assistant reply
        store.chatHistory.push({ role:'assistant', text: resp.data.answer })
      } catch (err) {
        // show whatever the backend sent - makes debugging easier
        const serverMsg = err.response?.data?.detail
          ? JSON.stringify(err.response.data.detail)
          : err.message

        store.chatHistory.push({ role:'assistant', text:`Error: ${serverMsg}` })

        // also log to console
        console.error('[Chatbot] request failed:', err)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
/* header strip */
.chat-header {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #2255aa;        /* bright blue */
}

.chat-header h2 {
  margin: 0 0 0 12px;
  color: #ffeb3b;             /* bright yellow text */
  font-size: 1.4em;
}

.back-button {
  background: none;
  border: none;
  color: #ffeb3b;
  font-size: 1.2em;
  cursor: pointer;
}

/* layout */
.chatbot-view {                   
  display:flex; flex-direction:column; height:100%;
}
.scroll-area { flex:1; overflow-y:auto; }
.composer {
  flex:none;
  box-shadow:0 -1px 4px rgba(0,0,0,.15);
}
</style>