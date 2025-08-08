#!/bin/bash
set -euo pipefail

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Portfolio Management System with uv + TailwindCSS セットアップ開始${NC}"

# 作業ディレクトリを確認（正しいパス）
WORKSPACE_ROOT="/workspaces/$(basename "${PWD}")"
cd "${WORKSPACE_ROOT}"

echo -e "${BLUE}📍 Working directory: ${WORKSPACE_ROOT}${NC}"

# 1. uv のインストール（最新版を確実にインストール）
echo -e "${BLUE}📦 Installing/updating uv...${NC}"
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/home/vscode/.cargo/bin:$PATH"
    echo 'export PATH="/home/vscode/.cargo/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="/home/vscode/.cargo/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
else
    echo -e "${GREEN}✅ uv already installed${NC}"
fi

# PATH を確実に設定
export PATH="/home/vscode/.cargo/bin:$PATH"

# 2. プロジェクトルート仮想環境のセットアップ
echo -e "${BLUE}🐍 Setting up root Python environment with uv...${NC}"
if [ ! -d ".venv" ]; then
    uv venv .venv --python 3.12
    echo -e "${GREEN}✅ Root virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️ Root .venv already exists${NC}"
fi

# 3. data-collector のセットアップ
if [ -d "data-collector" ]; then
    echo -e "${BLUE}📊 Setting up data-collector with uv...${NC}"
    cd data-collector
    
    if [ -f "pyproject.toml" ]; then
        uv sync --dev
        echo -e "${GREEN}✅ Data collector dependencies installed with uv${NC}"
    else
        echo -e "${RED}❌ pyproject.toml not found in data-collector${NC}"
    fi
    
    cd "${WORKSPACE_ROOT}"
fi

# 4. Backend のセットアップ
if [ -d "web-app/backend" ]; then
    echo -e "${BLUE}🔧 Setting up Django backend with uv...${NC}"
    
    # 👈 backendディレクトリに移動してからuv syncを実行するように修正
    cd web-app/backend

    # README.md がなければ作成する
    if [ ! -f "README.md" ]; then
        echo "# Backend README" > README.md
        echo -e "${GREEN}✅ Created dummy README.md in backend${NC}"
    fi
    
    if [ -f "pyproject.toml" ]; then
        uv sync --dev
        echo -e "${GREEN}✅ Backend dependencies installed with uv${NC}"
    elif [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
        echo -e "${GREEN}✅ Backend dependencies installed from requirements.txt${NC}"
    else
        echo -e "${RED}❌ No dependency file found in backend${NC}"
    fi

    cd "${WORKSPACE_ROOT}"
fi

# 5. Frontend のセットアップ（TailwindCSS含む）
if [ -d "web-app/frontend" ]; then
    echo -e "${BLUE}🎨 Setting up Vue.js frontend with TailwindCSS...${NC}"
    cd web-app/frontend
    
    # Node.js のバージョン確認
    echo -e "${BLUE}📋 Node.js version: $(node --version)${NC}"
    echo -e "${BLUE}📋 npm version: $(npm --version)${NC}"
    
    # 依存関係のインストール
    # package-lock.json との不整合でエラーになることがあるため、npm ci ではなく npm install を使用する
    npm install
    
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
    
    # TailwindCSS がインストールされているかチェック
    if npm list tailwindcss >/dev/null 2>&1; then
        echo -e "${GREEN}✅ TailwindCSS already installed${NC}"
    else
        echo -e "${YELLOW}⚠️ TailwindCSS not found - will be installed later${NC}"
    fi
    
    cd "${WORKSPACE_ROOT}"
fi

# gcloud CLI のインストール
if ! command -v gcloud >/dev/null 2>&1; then
    echo -e "${BLUE}📦 Installing Google Cloud CLI...${NC}"
    # ホームディレクトリにインストール
    curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=$HOME
    # PATHを通す
    echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
    # 現在のセッションにもPATHを適用
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    # gcloudの初期化（非対話モード）
    $HOME/google-cloud-sdk/bin/gcloud config set core/disable_usage_reporting true
    $HOME/google-cloud-sdk/bin/gcloud config set component_manager/disable_update_check true
    echo -e "${GREEN}✅ Google Cloud CLI installed${NC}"
else
    echo -e "${GREEN}✅ Google Cloud CLI already installed${NC}"
fi

# 6. Git 設定の改善
echo -e "${BLUE}🔧 Configuring Git...${NC}"
git config --global --add safe.directory "${WORKSPACE_ROOT}"
git config --global init.defaultBranch main
git config --global core.autocrlf false
git config --global core.eol lf

# 7. Claude Code の詳細設定
echo -e "${BLUE}🤖 Setting up Claude Code environment...${NC}"
mkdir -p /home/vscode/.config/claude-code

# Claude Codeの設定ファイル作成
cat > /home/vscode/.config/claude-code/config.json << 'EOF'
{
  "workspace": {
    "autoSave": true,
    "formatOnSave": true
  },
  "python": {
    "useUv": true,
    "defaultInterpreter": ".venv/bin/python"
  },
  "frontend": {
    "framework": "vue",
    "cssFramework": "tailwindcss"
  }
}
EOF

# 8. 開発用の便利なエイリアス設定
echo -e "${BLUE}🔗 Setting up development aliases...${NC}"
cat >> ~/.bashrc << 'EOF'

# Portfolio Management Development Aliases
alias uvrun='uv run'
alias uvdev='uv run --dev'
alias dc-run='cd data-collector && uv run python main.py'
alias be-dev='cd web-app/backend && uv run python manage.py runserver'
alias fe-dev='cd web-app/frontend && npm run dev'
alias proj-root='cd /workspaces/spreadsheet-chart-vue'

# uv shortcuts
alias uv-sync='uv sync --dev'
alias uv-add='uv add'
alias uv-check='uv run ruff check && uv run mypy .'

# Google Cloud shortcuts
alias gcloud-deploy='cd web-app/backend && gcloud builds submit --config cloudbuild.yaml'
alias gcloud-status='gcloud run services list --regions=asia-northeast1'
alias gcloud-logs='gcloud run logs tail portfolio-backend --region=asia-northeast1'
EOF

# 9. エディタ設定の改善
if [ ! -f ".editorconfig" ]; then
    echo -e "${BLUE}📝 Creating enhanced .editorconfig...${NC}"
    cat > .editorconfig << 'EOF'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,pyi}]
indent_style = space
indent_size = 4
max_line_length = 88

[*.{js,jsx,ts,tsx,vue,json,yml,yaml,css,scss,html}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
max_line_length = off

[Dockerfile*]
indent_style = tab
indent_size = 4
EOF
fi

# 10. Prettier設定の作成
if [ ! -f "web-app/frontend/.prettierrc" ] && [ -d "web-app/frontend" ]; then
    echo -e "${BLUE}💅 Creating Prettier configuration...${NC}"
    cat > web-app/frontend/.prettierrc << 'EOF'
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "endOfLine": "lf",
  "vueIndentScriptAndStyle": true
}
EOF
fi

# 11. 権限設定の改善
echo -e "${BLUE}🔐 Setting proper permissions...${NC}"
sudo chown -R vscode:vscode /home/vscode/.cache 2>/dev/null || true
sudo chown -R vscode:vscode /home/vscode/.cargo 2>/dev/null || true
sudo chown -R vscode:vscode "${WORKSPACE_ROOT}" 2>/dev/null || true

# キャッシュディレクトリの作成
mkdir -p /home/vscode/.cache/uv
mkdir -p /home/vscode/.cache/npm
chmod -R 755 /home/vscode/.cache

# 12. 開発環境の検証
echo -e "${BLUE}🔍 Verifying development environment...${NC}"
echo -e "${BLUE}📋 Python: $(python3 --version)${NC}"
echo -e "${BLUE}📋 uv: $(uv --version)${NC}"
echo -e "${BLUE}📋 Node.js: $(node --version)${NC}"
echo -e "${BLUE}📋 npm: $(npm --version)${NC}"

# 13. セットアップ完了メッセージ
echo -e "${GREEN}✨ セットアップ完了！${NC}"
echo -e "${YELLOW}💡 開発コマンド:${NC}"
echo "  📊 Data Collector: dc-run または cd data-collector && uv run python main.py"
echo "  🔧 Backend: be-dev または cd web-app/backend && uv run python manage.py runserver"
echo "  🎨 Frontend: fe-dev または cd web-app/frontend && npm run dev"
echo ""
echo -e "${YELLOW}🔧 便利なコマンド:${NC}"
echo "  📂 Project Root: proj-root"
echo "  🐍 uv sync: uv-sync"
echo "  ✅ Code Check: uv-check"
echo "  ☁️ Cloud Deploy: gcloud-deploy"
echo "  📊 Cloud Status: gcloud-status"
echo "  📝 Cloud Logs: gcloud-logs"
echo ""
echo -e "${BLUE}🌐 アクセスURL:${NC}"
echo "  Frontend: http://localhost:3000"
echo "  Backend: http://localhost:8000"
echo ""
echo -e "${GREEN}🎉 Happy Coding with uv + Vue.js + TailwindCSS! ${NC}"
