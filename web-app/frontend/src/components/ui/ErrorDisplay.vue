<template>
  <div class="error-display" :class="errorType">
    <div class="error-content">
      <!-- エラーアイコン -->
      <div class="error-icon">
        <span v-if="errorType === 'network'">🌐</span>
        <span v-else-if="errorType === 'auth'">🔐</span>
        <span v-else-if="errorType === 'data'">📊</span>
        <span v-else-if="errorType === 'validation'">⚠️</span>
        <span v-else>❌</span>
      </div>
      
      <!-- エラー情報 -->
      <div class="error-info">
        <h3 class="error-title">{{ errorTitle }}</h3>
        <p class="error-message">{{ message }}</p>
        
        <!-- 詳細情報（開発環境のみ） -->
        <div v-if="showDetails && details" class="error-details">
          <button @click="showDetailsExpanded = !showDetailsExpanded" class="details-toggle">
            {{ showDetailsExpanded ? '詳細を隠す' : '詳細を表示' }}
          </button>
          <div v-if="showDetailsExpanded" class="details-content">
            <pre>{{ details }}</pre>
          </div>
        </div>
        
        <!-- 推奨アクション -->
        <div v-if="recommendations.length > 0" class="error-recommendations">
          <h4>解決方法:</h4>
          <ul>
            <li v-for="(rec, index) in recommendations" :key="index">{{ rec }}</li>
          </ul>
        </div>
      </div>
    </div>
    
    <!-- アクションボタン -->
    <div class="error-actions">
      <button v-if="retryable" @click="$emit('retry')" class="retry-button" :disabled="retrying">
        <span v-if="retrying">🔄</span>
        {{ retrying ? '再試行中...' : '再試行' }}
      </button>
      
      <button v-if="contactSupport" @click="$emit('contact-support')" class="support-button">
        サポートに連絡
      </button>
      
      <button @click="$emit('dismiss')" class="dismiss-button">
        閉じる
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  message: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'generic',
    validator: value => ['network', 'auth', 'data', 'validation', 'generic'].includes(value)
  },
  details: {
    type: String,
    default: null
  },
  retryable: {
    type: Boolean,
    default: true
  },
  retrying: {
    type: Boolean,
    default: false
  },
  contactSupport: {
    type: Boolean,
    default: false
  },
  showDetails: {
    type: Boolean,
    default: import.meta.env.DEV // 開発環境でのみ詳細表示
  }
})

const emit = defineEmits(['retry', 'contact-support', 'dismiss'])

const showDetailsExpanded = ref(false)

// エラータイプに基づくUI設定
const errorType = computed(() => props.type)

const errorTitle = computed(() => {
  switch (props.type) {
    case 'network':
      return 'ネットワークエラー'
    case 'auth':
      return '認証エラー'
    case 'data':
      return 'データエラー'
    case 'validation':
      return 'データ検証エラー'
    default:
      return 'エラーが発生しました'
  }
})

const recommendations = computed(() => {
  switch (props.type) {
    case 'network':
      return [
        'インターネット接続を確認してください',
        'VPNや企業ファイアウォールの設定を確認してください',
        '少し時間をおいてから再試行してください'
      ]
    case 'auth':
      return [
        'ログイン情報を確認してください',
        'ページを更新してみてください',
        'アカウント管理者に連絡してください'
      ]
    case 'data':
      return [
        'Google Sheetsのアクセス権限を確認してください',
        'スプレッドシートのデータ形式を確認してください',
        'データが更新されるまで少しお待ちください'
      ]
    case 'validation':
      return [
        'データの入力形式を確認してください',
        '必須項目が入力されているか確認してください',
        '日付や数値の形式が正しいか確認してください'
      ]
    default:
      return [
        'ページを更新してみてください',
        '少し時間をおいてから再試行してください'
      ]
  }
})
</script>

<style scoped>
.error-display {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  margin: 20px 0;
  overflow: hidden;
  border-top: 4px solid;
}

.error-display.network {
  border-top-color: #f59e0b;
}

.error-display.auth {
  border-top-color: #ef4444;
}

.error-display.data {
  border-top-color: #8b5cf6;
}

.error-display.validation {
  border-top-color: #f59e0b;
}

.error-display.generic {
  border-top-color: #6b7280;
}

.error-content {
  display: flex;
  gap: 16px;
  padding: 20px;
}

.error-icon {
  font-size: 2rem;
  flex-shrink: 0;
  opacity: 0.8;
}

.error-info {
  flex: 1;
}

.error-title {
  margin: 0 0 8px 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #374151;
}

.error-message {
  margin: 0 0 16px 0;
  color: #6b7280;
  line-height: 1.5;
}

.error-details {
  margin: 16px 0;
}

.details-toggle {
  background: transparent;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 0.875rem;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.details-toggle:hover {
  border-color: #9ca3af;
  color: #374151;
}

.details-content {
  margin-top: 8px;
  background-color: #f9fafb;
  border-radius: 4px;
  padding: 12px;
  border: 1px solid #e5e7eb;
}

.details-content pre {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-recommendations {
  margin-top: 16px;
}

.error-recommendations h4 {
  margin: 0 0 8px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.error-recommendations ul {
  margin: 0;
  padding-left: 20px;
  color: #6b7280;
}

.error-recommendations li {
  margin: 4px 0;
  line-height: 1.4;
}

.error-actions {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  background-color: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.error-actions button {
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.retry-button {
  background-color: #3b82f6;
  color: white;
}

.retry-button:hover:not(:disabled) {
  background-color: #2563eb;
}

.retry-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.support-button {
  background-color: #10b981;
  color: white;
}

.support-button:hover {
  background-color: #059669;
}

.dismiss-button {
  background-color: #6b7280;
  color: white;
  margin-left: auto;
}

.dismiss-button:hover {
  background-color: #4b5563;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .error-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .dismiss-button {
    margin-left: 0;
  }
}
</style>