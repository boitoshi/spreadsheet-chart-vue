<template>
  <div id="app">
    <nav class="navbar">
      <router-link to="/" class="nav-link">ダッシュボード</router-link>
      <router-link to="/input" class="nav-link">手動入力</router-link>
      <router-link to="/report/2024-01" class="nav-link">月次レポート</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
#app {
  min-height: 100vh;
  background: #f8f9fa;
}

.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem 2rem;
  display: flex;
  gap: 2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  transition: background-color 0.3s ease;
  font-weight: 500;
}

.nav-link:hover,
.nav-link.router-link-active {
  background-color: rgba(255,255,255,0.2);
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
}
</style>
