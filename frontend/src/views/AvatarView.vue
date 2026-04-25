<script setup lang="ts">
import { ref } from 'vue'

// 这个页面的状态主要围绕“上传素材”和“触发生成”两步展开。
const avatarId = ref('')
const selectedFile = ref<File | null>(null)
const uploadStatus = ref<'idle' | 'uploading' | 'uploaded' | 'generating' | 'success' | 'error'>('idle')
const backendFilename = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const onFileChange = (e: Event) => {
  // 统一处理点击选择和拖拽上传两种入口。
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    selectedFile.value = target.files[0]
    uploadStatus.value = 'idle'
  }
}

const handleUpload = async () => {
  // 第一步：把原始素材先传到后端 `data/uploads/` 目录。
  if (!selectedFile.value || !avatarId.value) {
    errorMessage.value = '请输入形象ID并选择文件'
    return
  }

  uploadStatus.value = 'uploading'
  errorMessage.value = ''
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const res = await fetch('/api/v1/upload', {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    
    if (data.code === 0) {
      backendFilename.value = data.data.filename
      uploadStatus.value = 'uploaded'
      successMessage.value = '文件上传成功，准备开始处理'
    } else {
      throw new Error(data.msg || '上传失败')
    }
  } catch (err: any) {
    uploadStatus.value = 'error'
    errorMessage.value = err.message
  }
}

const handleGenerate = async () => {
  // 第二步：通知后端基于刚上传的素材生成 avatar 数据。
  if (!avatarId.value || !backendFilename.value) return

  uploadStatus.value = 'generating'
  errorMessage.value = ''

  try {
    const res = await fetch('/api/v1/avatar/gen', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        avatar_id: avatarId.value,
        filename: backendFilename.value
      })
    })
    const data = await res.json()

    if (data.code === 0) {
      uploadStatus.value = 'success'
      successMessage.value = '训练任务已启动！请在后端数据目录查看结果。'
    } else {
      throw new Error(data.msg || '生成失败')
    }
  } catch (err: any) {
    uploadStatus.value = 'error'
    errorMessage.value = err.message
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#FDFDFF] p-6 lg:p-12 font-sans selection:bg-indigo-100 selection:text-indigo-900">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <header class="mb-12 animate-in fade-in slide-in-from-top-4 duration-700">
        <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight mb-3">
          Avatar <span class="bg-clip-text text-transparent bg-linear-to-r from-indigo-600 to-violet-600">Studio</span>
        </h1>
        <p class="text-gray-500 text-lg max-w-2xl">
          建立属于您的数字形象。上传一段短视频或照片，让 LiveTalking 赋予它生命。
        </p>
      </header>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <!-- Main Form Section -->
        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white rounded-3xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 transition-all hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)]">
            
            <!-- Avatar ID Input -->
            <div class="mb-8">
              <label for="avatarId" class="block text-sm font-semibold text-gray-700 mb-2 ml-1">形象唯一标识 (ID)</label>
              <input 
                v-model="avatarId"
                id="avatarId"
                type="text" 
                placeholder="例如: kunkun_v2"
                class="w-full px-5 py-4 bg-gray-50 border-transparent focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-50 rounded-2xl transition-all duration-200 text-gray-900 font-medium outline-none"
              />
            </div>

            <!-- File Upload Zone -->
            <div class="mb-8">
              <label class="block text-sm font-semibold text-gray-700 mb-2 ml-1">素材上传 (MP4, PNG, JPG)</label>
              <div 
                class="relative group cursor-pointer"
                @click="(($refs.fileInput as HTMLInputElement).click())"
                @dragover.prevent
                @drop.prevent="(e) => onFileChange({ target: { files: e.dataTransfer?.files } } as any)"
              >
                <input 
                  ref="fileInput"
                  type="file" 
                  class="hidden" 
                  accept="video/*,image/*"
                  @change="onFileChange"
                />
                
                <div 
                  class="border-2 border-dashed rounded-3xl p-12 flex flex-col items-center justify-center transition-all duration-300"
                  :class="[
                    selectedFile ? 'border-green-200 bg-green-50/30' : 'border-gray-200 bg-gray-50 group-hover:border-indigo-300 group-hover:bg-indigo-50/30'
                  ]"
                >
                  <div class="w-16 h-16 rounded-2xl bg-white shadow-sm flex items-center justify-center mb-4 transition-transform group-hover:scale-110 duration-300">
                    <svg v-if="!selectedFile" xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  
                  <p class="text-sm font-bold text-gray-900 mb-1">
                    {{ selectedFile ? selectedFile.name : '点击或拖拽文件到这里' }}
                  </p>
                  <p class="text-xs text-gray-500">
                    支持 MP4 视频或单张高清照片
                  </p>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex flex-col sm:flex-row gap-4">
              <button 
                @click="handleUpload"
                :disabled="!selectedFile || uploadStatus === 'uploading' || uploadStatus === 'uploaded'"
                class="flex-1 py-4 px-6 rounded-2xl font-bold transition-all duration-200 flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 disabled:shadow-none"
                :class="[
                  uploadStatus === 'uploaded' 
                    ? 'bg-green-500 text-white cursor-default' 
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200'
                ]"
              >
                <svg v-if="uploadStatus === 'uploading'" class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span v-if="uploadStatus === 'uploading'">正在上传...</span>
                <span v-else-if="['uploaded', 'generating', 'success'].includes(uploadStatus)">上传成功</span>
                <span v-else>立即上传素材</span>
              </button>

              <button 
                @click="handleGenerate"
                :disabled="uploadStatus !== 'uploaded'"
                class="flex-1 py-4 px-6 rounded-2xl font-bold transition-all duration-200 border-2 flex items-center justify-center gap-2"
                :class="[
                  uploadStatus === 'uploaded'
                    ? 'border-indigo-600 text-indigo-600 hover:bg-indigo-50 shadow-sm'
                    : 'border-gray-200 text-gray-400 cursor-not-allowed'
                ]"
              >
                 <svg v-if="uploadStatus === 'generating'" class="animate-spin h-5 w-5 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span v-if="uploadStatus === 'generating'">正在训练中...</span>
                <span v-else>点击开始生成</span>
              </button>
            </div>

            <!-- Feedback Messages -->
            <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 translate-y-2" enter-to-class="opacity-100 translate-y-0">
              <div v-if="errorMessage" class="mt-6 p-4 rounded-2xl bg-red-50 border border-red-100 flex items-center gap-3 text-red-600 text-sm font-medium">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                {{ errorMessage }}
              </div>
            </Transition>
            
            <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 translate-y-2" enter-to-class="opacity-100 translate-y-0">
              <div v-if="successMessage" class="mt-6 p-4 rounded-2xl bg-green-50 border border-green-100 flex items-center gap-3 text-green-700 text-sm font-medium">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                {{ successMessage }}
              </div>
            </Transition>
          </div>
        </div>

        <!-- Info Sidebar -->
        <div class="space-y-6">
          <div class="bg-indigo-900 rounded-3xl p-6 text-white shadow-xl shadow-indigo-200/50">
            <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-300" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zm-1 9a1 1 0 00-1 1v-4a1 1 0 102 0v4a1 1 0 00-1 1z" clip-rule="evenodd" />
              </svg>
              上传指南
            </h3>
            <ul class="space-y-4 text-sm text-indigo-100/80 leading-relaxed">
              <li>
                <strong class="text-white">视频素材</strong>：建议 30-60 秒左右，平视镜头说话，背景简洁，光线充足。
              </li>
              <li>
                <strong class="text-white">训练时间</strong>：生成过程取决于 GPU 硬件性能，通常需要几分钟。
              </li>
              <li>
                <strong class="text-white">命名规则</strong>：ID 仅限英文、数字和下划线。
              </li>
            </ul>
          </div>
          
          <router-link to="/chat" class="block group">
            <div class="bg-gray-100 hover:bg-gray-200 rounded-3xl p-6 transition-all duration-300 flex items-center justify-between">
              <div>
                <p class="text-gray-900 font-bold mb-0.5">返回对话</p>
                <p class="text-gray-500 text-xs text-nowrap">前往数字人直播间</p>
              </div>
              <div class="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm group-hover:translate-x-1 transition-transform">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-700" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Glassmorphism effects or extra animations if needed */
</style>
