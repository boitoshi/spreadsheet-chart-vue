<template>
    <div>
      <h2>Googleスプレッドシートのデータ</h2>
      <ul>
        <li v-for="(row, index) in sheetData" :key="index">
          {{ row }}
        </li>
      </ul>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  
  const sheetData = ref([]) // APIで取得したデータを格納する変数
  
  onMounted(async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/sheets_api/get_data/') // Djangoのエンドポイント
      if (!response.ok) {
        throw new Error('API呼び出しに失敗しました')
      }
      sheetData.value = await response.json() // データを取得して保存
    } catch (error) {
      console.error('エラー:', error)
    }
  })
  </script>
  
  <style scoped>
  h2 {
    text-align: center;
  }
  </style>
