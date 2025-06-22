<template>
    <div>
      <h2>損益テーブル</h2>
      <table>
        <thead>
          <tr>
            <th>銘柄名</th>
            <th>取得価格</th>
            <th>報告月末価格</th>
            <th>取得株数</th>
            <th>損益</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stock in stockTableData" :key="stock.name">
            <td>{{ stock.name }}</td>
            <td>{{ stock.acquisitionPrice }}</td>
            <td>{{ stock.finalPrice }}</td>
            <td>{{ stock.shares }}</td>
            <td :class="{ profit: stock.profitLoss > 0, loss: stock.profitLoss < 0 }">
              {{ stock.profitLoss }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script setup>
  import { ref } from "vue";
  
  // 仮の損益データ
  const stockTableData = ref([
    { name: "DeNA", acquisitionPrice: 2000, finalPrice: 2100, shares: 3, profitLoss: 300 },
    { name: "任天堂", acquisitionPrice: 5500, finalPrice: 5600, shares: 2, profitLoss: 200 },
  ]);
  </script>
  
  <style scoped>
  h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 0 auto;
  }
  
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
  }
  
  th {
    background-color: #f4f4f4;
    font-weight: bold;
  }
  
  .profit {
    color: green;
  }
  
  .loss {
    color: red;
  }
  </style>
