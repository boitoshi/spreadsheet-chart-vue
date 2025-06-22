<template>
  <div class="manual-input-container">
    <div class="input-header">
      <h1>📝 手動データ入力</h1>
      <p>株価データを手動で入力・更新できます</p>
    </div>
    
    <div class="input-content">
      <!-- 銘柄検索・追加セクション -->
      <section class="search-section">
        <h2>🔍 銘柄検索・追加</h2>
        <div class="search-form">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="銘柄コードまたは会社名を入力"
            class="search-input"
          >
          <button @click="searchStock" class="search-button">検索</button>
        </div>
        
        <div v-if="searchResults.length > 0" class="search-results">
          <div 
            v-for="stock in searchResults" 
            :key="stock.ticker"
            @click="selectStock(stock)"
            class="search-result-item"
          >
            <span class="stock-ticker">{{ stock.ticker }}</span>
            <span class="stock-name">{{ stock.name }}</span>
            <span class="stock-price">¥{{ stock.price.toLocaleString() }}</span>
          </div>
        </div>
      </section>
      
      <!-- 価格入力セクション -->
      <section class="price-input-section">
        <h2>💰 価格データ入力</h2>
        <div class="input-form">
          <div class="form-row">
            <label>銘柄</label>
            <select v-model="selectedStock" class="form-select">
              <option value="">銘柄を選択してください</option>
              <option 
                v-for="stock in portfolioStocks" 
                :key="stock.ticker"
                :value="stock.ticker"
              >
                {{ stock.ticker }} - {{ stock.name }}
              </option>
            </select>
          </div>
          
          <div class="form-row">
            <label>日付</label>
            <input 
              v-model="inputDate" 
              type="date"
              class="form-input"
            >
          </div>
          
          <div class="form-row">
            <label>価格（円）</label>
            <input 
              v-model.number="inputPrice" 
              type="number" 
              step="0.01"
              placeholder="価格を入力"
              class="form-input"
            >
          </div>
          
          <div class="form-row">
            <label>数量</label>
            <input 
              v-model.number="inputQuantity" 
              type="number"
              placeholder="株数を入力"
              class="form-input"
            >
          </div>
          
          <div class="form-row">
            <label>取引種別</label>
            <select v-model="transactionType" class="form-select">
              <option value="buy">買い</option>
              <option value="sell">売り</option>
              <option value="update">価格更新</option>
            </select>
          </div>
          
          <button @click="submitData" class="submit-button">
            データを保存
          </button>
        </div>
      </section>
      
      <!-- 最近の入力履歴 -->
      <section class="history-section">
        <h2>📋 最近の入力履歴</h2>
        <div class="history-table">
          <table>
            <thead>
              <tr>
                <th>日付</th>
                <th>銘柄</th>
                <th>種別</th>
                <th>価格</th>
                <th>数量</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in inputHistory" :key="entry.id">
                <td>{{ formatDate(entry.date) }}</td>
                <td>{{ entry.ticker }} - {{ entry.name }}</td>
                <td>
                  <span :class="getTransactionClass(entry.type)">
                    {{ getTransactionLabel(entry.type) }}
                  </span>
                </td>
                <td>¥{{ entry.price.toLocaleString() }}</td>
                <td>{{ entry.quantity }}株</td>
                <td>
                  <button @click="editEntry(entry)" class="edit-button">編集</button>
                  <button @click="deleteEntry(entry.id)" class="delete-button">削除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      
      <!-- 一括インポート -->
      <section class="import-section">
        <h2>📤 一括インポート</h2>
        <div class="import-form">
          <div class="file-upload">
            <input 
              ref="fileInput"
              type="file" 
              @change="handleFileUpload"
              accept=".csv,.xlsx"
              style="display: none"
            >
            <button @click="$refs.fileInput.click()" class="upload-button">
              CSVファイルを選択
            </button>
            <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
          </div>
          
          <div class="csv-format-info">
            <h4>CSVフォーマット例：</h4>
            <pre>日付,銘柄コード,銘柄名,価格,数量,取引種別
2024-01-15,7974,任天堂,6500,100,buy
2024-01-16,2432,DeNA,2380,50,buy</pre>
          </div>
          
          <button @click="importData" :disabled="!selectedFile" class="import-button">
            データをインポート
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'

export default {
  name: 'ManualInput',
  setup() {
    const searchQuery = ref('')
    const searchResults = ref([])
    const selectedStock = ref('')
    const inputDate = ref(new Date().toISOString().split('T')[0])
    const inputPrice = ref(null)
    const inputQuantity = ref(null)
    const transactionType = ref('buy')
    const selectedFile = ref(null)
    const portfolioStocks = ref([])
    const inputHistory = ref([])
    
    // サンプルデータ
    const sampleStocks = [
      { ticker: '7974', name: '任天堂', price: 6500 },
      { ticker: '2432', name: 'DeNA', price: 2380 },
      { ticker: 'AAPL', name: 'Apple Inc.', price: 28000 },
      { ticker: '6758', name: 'ソニーグループ', price: 13500 },
      { ticker: '9984', name: 'ソフトバンクグループ', price: 7200 }
    ]
    
    const sampleHistory = [
      {
        id: 1,
        date: '2024-01-15',
        ticker: '7974',
        name: '任天堂',
        type: 'buy',
        price: 6500,
        quantity: 100
      },
      {
        id: 2,
        date: '2024-01-16',
        ticker: '2432',
        name: 'DeNA',
        type: 'buy',
        price: 2380,
        quantity: 50
      }
    ]
    
    const searchStock = () => {
      if (!searchQuery.value.trim()) {
        searchResults.value = []
        return
      }
      
      // 実際の実装では API を呼び出す
      searchResults.value = sampleStocks.filter(stock => 
        stock.ticker.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        stock.name.includes(searchQuery.value)
      )
    }
    
    const selectStock = (stock) => {
      selectedStock.value = stock.ticker
      searchQuery.value = ''
      searchResults.value = []
    }
    
    const submitData = async () => {
      if (!selectedStock.value || !inputPrice.value || !inputQuantity.value) {
        alert('必須項目を入力してください')
        return
      }
      
      const newEntry = {
        id: Date.now(),
        date: inputDate.value,
        ticker: selectedStock.value,
        name: portfolioStocks.value.find(s => s.ticker === selectedStock.value)?.name || '',
        type: transactionType.value,
        price: inputPrice.value,
        quantity: inputQuantity.value
      }
      
      inputHistory.value.unshift(newEntry)
      
      // フォームリセット
      inputPrice.value = null
      inputQuantity.value = null
      
      alert('データが保存されました')
      
      // 実際の実装では API に送信
      console.log('Submitting data:', newEntry)
    }
    
    const editEntry = (entry) => {
      selectedStock.value = entry.ticker
      inputDate.value = entry.date
      inputPrice.value = entry.price
      inputQuantity.value = entry.quantity
      transactionType.value = entry.type
    }
    
    const deleteEntry = (id) => {
      if (confirm('この入力データを削除しますか？')) {
        inputHistory.value = inputHistory.value.filter(entry => entry.id !== id)
      }
    }
    
    const handleFileUpload = (event) => {
      selectedFile.value = event.target.files[0]
    }
    
    const importData = () => {
      if (!selectedFile.value) return
      
      // 実際の実装では CSV パーサーを使用
      alert('CSVインポート機能は実装中です')
      console.log('Importing file:', selectedFile.value.name)
    }
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return `${date.getFullYear()}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`
    }
    
    const getTransactionClass = (type) => {
      switch (type) {
        case 'buy': return 'transaction-buy'
        case 'sell': return 'transaction-sell'
        case 'update': return 'transaction-update'
        default: return ''
      }
    }
    
    const getTransactionLabel = (type) => {
      switch (type) {
        case 'buy': return '買い'
        case 'sell': return '売り'
        case 'update': return '更新'
        default: return type
      }
    }
    
    onMounted(() => {
      portfolioStocks.value = sampleStocks
      inputHistory.value = sampleHistory
    })
    
    return {
      searchQuery,
      searchResults,
      selectedStock,
      inputDate,
      inputPrice,
      inputQuantity,
      transactionType,
      selectedFile,
      portfolioStocks,
      inputHistory,
      searchStock,
      selectStock,
      submitData,
      editEntry,
      deleteEntry,
      handleFileUpload,
      importData,
      formatDate,
      getTransactionClass,
      getTransactionLabel
    }
  }
}
</script>

<style scoped>
.manual-input-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.input-header {
  text-align: center;
  margin-bottom: 40px;
}

.input-header h1 {
  color: #333;
  margin-bottom: 10px;
}

.input-header p {
  color: #666;
  font-size: 1.1em;
}

.input-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* セクション共通スタイル */
section {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}

section h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 1.3em;
}

/* 検索セクション */
.search-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 12px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.search-button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.search-button:hover {
  background: #5a6fd8;
}

.search-results {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.search-result-item:hover {
  background: #f8f9fa;
}

.search-result-item:last-child {
  border-bottom: none;
}

.stock-ticker {
  font-weight: 600;
  color: #667eea;
}

.stock-name {
  flex: 1;
  margin-left: 15px;
}

.stock-price {
  font-weight: 600;
  color: #333;
}

/* フォームスタイル */
.input-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-row label {
  font-weight: 600;
  color: #333;
}

.form-input,
.form-select {
  padding: 12px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
}

.submit-button {
  padding: 15px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  margin-top: 10px;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

/* 履歴テーブル */
.history-table {
  overflow-x: auto;
}

.history-table table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #e9ecef;
}

.history-table td {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
}

.history-table tr:hover {
  background: #f8f9fa;
}

.transaction-buy {
  color: #4CAF50;
  font-weight: 600;
}

.transaction-sell {
  color: #f44336;
  font-weight: 600;
}

.transaction-update {
  color: #2196F3;
  font-weight: 600;
}

.edit-button,
.delete-button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 5px;
}

.edit-button {
  background: #2196F3;
  color: white;
}

.delete-button {
  background: #f44336;
  color: white;
}

.edit-button:hover,
.delete-button:hover {
  opacity: 0.8;
}

/* インポートセクション */
.import-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.file-upload {
  display: flex;
  align-items: center;
  gap: 15px;
}

.upload-button {
  padding: 12px 24px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.upload-button:hover {
  background: #218838;
}

.file-name {
  color: #666;
  font-style: italic;
}

.csv-format-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.csv-format-info h4 {
  margin-bottom: 10px;
  color: #333;
}

.csv-format-info pre {
  background: white;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

.import-button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.import-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.import-button:not(:disabled):hover {
  background: #5a6fd8;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .search-form {
    flex-direction: column;
  }
  
  .search-result-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .history-table {
    font-size: 14px;
  }
  
  .history-table th,
  .history-table td {
    padding: 8px;
  }
  
  .file-upload {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>