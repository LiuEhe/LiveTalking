<template>
  <div class="flex h-screen bg-gray-50 text-gray-800 font-sans">
    <!-- Left Sidebar: Video streaming (1/3 width) -->
    <div class="w-1/3 min-w-[320px] bg-white border-r border-gray-200 flex flex-col shadow-sm z-10 relative">
      <div class="p-5 border-b border-gray-100 flex items-center justify-between bg-white/80 backdrop-blur-md sticky top-0">
        <h2 class="font-semibold text-lg text-gray-800 tracking-tight">LiveTalking <span class="font-normal text-gray-400 ml-1 text-sm">Avatar Stream</span></h2>
        <!-- Status Indicator -->
        <div class="flex items-center bg-gray-50 px-3 py-1.5 rounded-full border border-gray-100">
          <span 
            class="w-2 h-2 rounded-full mr-2 relative" 
            :class="{
              'bg-red-500': connectionStatus === 'disconnected',
              'bg-yellow-400': connectionStatus === 'connecting',
              'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]': connectionStatus === 'connected'
            }"
          >
            <span v-if="connectionStatus === 'connected'" class="absolute inset-0 rounded-full animate-ping bg-green-400 opacity-75"></span>
          </span>
          <span class="text-xs font-medium text-gray-600">
            {{ connectionStatus === 'connected' ? '已连接' : (connectionStatus === 'connecting' ? '连接中...' : '未连接') }}
          </span>
        </div>
      </div>
      
      <!-- Video Area -->
      <div class="p-5 flex flex-col space-y-5 grow overflow-y-auto">
        <div class="relative w-full aspect-3/4 bg-gray-900 rounded-2xl overflow-hidden shadow-lg border border-gray-800 group transition-all duration-300 hover:shadow-xl flex items-center justify-center">
          <!-- Video & Audio elements -->
          <video id="video" class="w-full h-full object-cover transition-opacity duration-300" :class="{'opacity-0': connectionStatus === 'disconnected', 'opacity-100': connectionStatus !== 'disconnected'}" autoplay playsinline></video>
          <audio id="audio" autoplay></audio>
          
          <!-- Disconnected Placeholder -->
          <div v-if="connectionStatus === 'disconnected'" class="absolute gap-4 flex flex-col items-center justify-center text-gray-500 transition-opacity duration-300">
            <div class="w-20 h-20 rounded-full bg-gray-800/50 flex items-center justify-center mb-2 shadow-inner border border-gray-700/50">
              <Video class="h-8 w-8 text-gray-600" />
            </div>
            <p class="text-sm font-medium tracking-wide">等待数字人推流接入</p>
          </div>
          
          <!-- Connecting state -->
          <div v-else-if="connectionStatus === 'connecting'" class="absolute inset-0 bg-gray-900/80 backdrop-blur-sm flex flex-col items-center justify-center z-10 transition-opacity duration-300">
            <Loader2 class="animate-spin h-10 w-10 text-white mb-4" />
            <span class="text-white text-sm font-medium tracking-widest uppercase">Connecting stream...</span>
          </div>
          
          <!-- Recording Overlay -->
          <div v-if="isRecording" class="absolute top-4 right-4 bg-red-500/90 text-white text-[11px] font-bold px-2.5 py-1 rounded-md flex items-center shadow-lg backdrop-blur-md uppercase tracking-wider">
            <span class="w-1.5 h-1.5 bg-white rounded-full mr-2 animate-ping"></span>
            录制中
          </div>
        </div>
        
        <!-- Stream Controls -->
        <div class="bg-gray-50/50 rounded-2xl p-4 border border-gray-100 flex flex-col gap-3.5 shadow-sm">
          <button 
            v-if="connectionStatus === 'disconnected'" 
            @click="startConnection"
            class="w-full py-3 bg-gray-900 hover:bg-black text-white rounded-xl font-medium transition-all duration-200 shadow-md hover:shadow-lg flex items-center justify-center gap-2 transform active:scale-[0.98]"
          >
            <Play class="h-5 w-5" />
            开始接收视频流
          </button>
          
          <button 
            v-else 
            @click="stopConnection"
            class="w-full py-3 bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
          >
            <Square class="h-5 w-5" />
            断开连接
          </button>
          
          <div class="flex gap-2">
            <button 
              @click="toggleRecording"
              :class="isRecording ? 'bg-red-50 text-red-600 border-red-200 hover:bg-red-100 ring-1 ring-red-500/20' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 border'"
              class="flex-1 py-2.5 rounded-xl text-[13px] font-medium transition-all flex items-center justify-center gap-2 shadow-sm"
            >
              <span class="w-2.5 h-2.5 rounded-full ring-2 ring-offset-1" :class="isRecording ? 'bg-red-500 ring-red-200 animate-pulse' : 'bg-red-500 ring-transparent'"></span>
              {{ isRecording ? '停止云端录制' : '开始云端录制' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Main Area: Chat Interface (2/3 width) -->
    <div class="w-2/3 flex flex-col relative bg-white flex-grow">
      <!-- Chat Messages Setup -->
      <div class="flex-1 overflow-y-auto p-6 md:px-12 md:py-8 space-y-6 scroll-smooth bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-50 via-white to-white">
        
        <!-- Empty state -->
        <div v-if="messages.length === 0" class="h-[80%] flex flex-col items-center justify-center text-gray-400 space-y-6 animate-in fade-in duration-700">
          <div class="w-20 h-20 bg-gray-50 rounded-3xl flex items-center justify-center text-gray-300 ring-1 ring-gray-100 shadow-sm rotate-3">
            <MessageSquare class="h-10 w-10 -rotate-3" />
          </div>
          <div class="text-center space-y-1">
            <h3 class="text-gray-800 font-medium text-lg">准备好开始对话了</h3>
            <p class="text-sm">在下方输入消息，或在移动端按住语音键说话</p>
          </div>
        </div>
        
        <!-- Message list -->
        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          class="flex w-full group animate-in slide-in-from-bottom-2 fade-in duration-300"
          :class="msg.type === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div 
            class="max-w-[80%] px-5 py-3.5 text-[15px] leading-relaxed relative"
            :class="[
              msg.type === 'user' 
                ? 'bg-gray-100 text-gray-900 rounded-3xl rounded-br-sm' 
                : (msg.type === 'system' 
                   ? 'bg-orange-50/80 text-orange-800 border border-orange-100/50 rounded-2xl w-full text-center text-[13px] mx-auto max-w-sm my-4 font-medium py-2 shadow-sm'
                   : 'text-gray-900 rounded-3xl rounded-bl-sm border border-transparent')
            ]"
          >
            <!-- Avatar for bot (optional) -->
            <div v-if="msg.type === 'bot'" class="absolute -left-10 top-1 w-7 h-7 bg-black rounded-full flex items-center justify-center shadow-sm">
               <Bot class="h-4 w-4 text-white" />
            </div>
            
            <span class="whitespace-pre-wrap">{{ msg.text }}</span>
          </div>
        </div>
      </div>
      
      <!-- Input Area -->
      <div class="px-6 pb-6 pt-2 md:px-12 md:pb-8 bg-gradient-to-t from-white via-white to-white/50 backdrop-blur-sm relative z-20">
        <div class="relative bg-white border border-gray-200 rounded-[28px] shadow-sm focus-within:shadow-md focus-within:border-gray-300 transition-all duration-300 group flex items-end">
          
          <!-- Voice Button -->
          <button 
            @mousedown="isRecording = true" 
            @mouseup="isRecording = false"
            @mouseleave="isRecording = false"
            class="p-4 text-gray-400 hover:text-black transition-colors rounded-full focus:outline-none flex-shrink-0"
            :class="{'text-black bg-gray-50': isRecording}"
            title="语音输入"
          >
            <Mic class="h-[22px] w-[22px]" />
          </button>
          
          <!-- Textarea -->
          <textarea 
            v-model="inputMessage" 
            @keydown.enter.prevent="sendMessage"
            rows="1" 
            class="w-full py-[18px] bg-transparent border-none focus:ring-0 resize-none text-[15px] max-h-32 placeholder-gray-400 leading-tight block font-sans"
            style="min-height: 56px;"
            placeholder="消息 LiveTalking 发送..."
          ></textarea>
          
          <!-- Send Button -->
          <div class="p-2 flex-shrink-0">
            <button 
              @click="sendMessage"
              :disabled="!inputMessage.trim()"
              class="w-10 h-10 rounded-full transition-all duration-300 focus:outline-none flex items-center justify-center transform disabled:opacity-30 disabled:cursor-not-allowed"
              :class="inputMessage.trim() ? 'bg-black text-white hover:scale-105 active:scale-95 shadow-md' : 'bg-gray-100 text-gray-400'"
            >
              <Send class="h-5 w-5 ml-0.5" />
            </button>
          </div>
        </div>
        
        <!-- Footer / Disclaimer -->
        <div class="text-center mt-4">
          <p class="text-xs text-gray-400 font-medium">
            LiveTalking 可以犯错。请核实重要信息。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { 
  Video, 
  Mic, 
  Play, 
  Square, 
  MessageSquare, 
  Send, 
  Bot, 
  Loader2 
} from 'lucide-vue-next'

const messages = ref([
  { id: 1, type: 'system', text: '欢迎使用livetalking，请点击"开始连接"按钮开始对话。' }
])
const inputMessage = ref('')
const connectionStatus = ref('disconnected') // disconnected, connecting, connected
const isRecording = ref(false)
const sessionId = ref(0)
let pc: RTCPeerConnection | null = null

const negotiate = async () => {
  if (!pc) return

  pc.addTransceiver('video', { direction: 'recvonly' })
  pc.addTransceiver('audio', { direction: 'recvonly' })
  
  const offer = await pc.createOffer()
  await pc.setLocalDescription(offer)
  
  // wait for ICE gathering
  await new Promise<void>((resolve) => {
    if (pc!.iceGatheringState === 'complete') {
      resolve()
    } else {
      const checkState = () => {
        if (pc!.iceGatheringState === 'complete') {
          pc!.removeEventListener('icegatheringstatechange', checkState)
          resolve()
        }
      }
      pc!.addEventListener('icegatheringstatechange', checkState)
    }
  })

  const localOffer = pc.localDescription
  if (!localOffer) return

  try {
    const res = await fetch('/api/v1/offer', {
      body: JSON.stringify({
        sdp: localOffer.sdp,
        type: localOffer.type,
      }),
      headers: {
        'Content-Type': 'application/json'
      },
      method: 'POST'
    })
    
    const answer = await res.json()
    sessionId.value = answer.sessionid
    await pc.setRemoteDescription(answer)
    connectionStatus.value = 'connected'
    console.log("WebRTC Connected. Session ID:", sessionId.value)
  } catch (e) {
    console.error('WebRTC negotiate error:', e)
    connectionStatus.value = 'disconnected'
    alert('连接失败：' + e)
  }
}

const startConnection = () => {
  connectionStatus.value = 'connecting'
  const config: RTCConfiguration = {
    sdpSemantics: 'unified-plan'
  } as any // Use unified-plan assuming modern browsers

  pc = new RTCPeerConnection(config)

  pc.addEventListener('track', (evt) => {
    if (evt.track.kind === 'video') {
      const videoEl = document.getElementById('video') as HTMLVideoElement
      if (videoEl) videoEl.srcObject = evt.streams[0]
    } else {
      const audioEl = document.getElementById('audio') as HTMLAudioElement
      if (audioEl) audioEl.srcObject = evt.streams[0]
    }
  })

  // Watch for disconnects properly
  pc.addEventListener('connectionstatechange', () => {
    if (pc?.connectionState === 'disconnected' || pc?.connectionState === 'failed') {
      connectionStatus.value = 'disconnected'
    }
  })

  negotiate()
}

const stopConnection = () => {
  connectionStatus.value = 'disconnected'
  if (pc) {
    pc.close()
    pc = null
  }
}

// Ensure cleanup goes through
onBeforeUnmount(() => {
  stopConnection()
})

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  const text = inputMessage.value
  messages.value.push({
    id: Date.now(),
    type: 'user',
    text: text
  })
  
  inputMessage.value = ''

  try {
    const res = await fetch('/api/v1/human', {
      body: JSON.stringify({
        text: text,
        type: 'chat',
        interrupt: true,
        sessionid: sessionId.value,
      }),
      headers: {
        'Content-Type': 'application/json'
      },
      method: 'POST'
    })

    if (!res.body) return
    
    // Preparation for bot streaming response
    const botMsgId = Date.now() + 1
    messages.value.push({
      id: botMsgId,
      type: 'bot',
      text: ''
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    
    let isFinished = false
    while (!isFinished) {
      const { done, value } = await reader.read()
      if (done) {
        isFinished = true
        break
      }
      
      const chunk = decoder.decode(value, { stream: true })
      const botMsg = messages.value.find(m => m.id === botMsgId)
      if (botMsg) {
        botMsg.text += chunk
      }
    }

  } catch (error) {
    console.error("Failed to send message", error)
  }
}

const toggleRecording = async () => {
  if (isRecording.value) {
    // Stop recording
    try {
      const res = await fetch('/api/v1/record', {
        body: JSON.stringify({
          type: 'end_record',
          sessionid: sessionId.value,
        }),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST'
      })
      if (res.ok) isRecording.value = false
    } catch (e) {
      console.error(e)
    }
  } else {
    // Start recording
    try {
      const res = await fetch('/api/v1/record', {
        body: JSON.stringify({
          type: 'start_record',
          sessionid: sessionId.value,
        }),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST'
      })
      if (res.ok) isRecording.value = true
    } catch (e) {
      console.error(e)
    }
  }
}
</script>

<style scoped>
/* 自定义滚动条风格以匹配美观的UI */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
  margin: 10px 0;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #E5E7EB;
  border-radius: 10px;
}
.overflow-y-auto:hover::-webkit-scrollbar-thumb {
  background-color: #D1D5DB;
}

/* 输入框重置边框轮廓 */
textarea:focus {
  outline: none;
}
</style>
