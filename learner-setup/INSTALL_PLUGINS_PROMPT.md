# TWS AI 課程環境建置 Prompt

將以下內容貼到新的 Codex 任務。Codex 會自動辨識 macOS 或 Windows，依 manifest 檢查 13 個不需外部帳號登入的外掛，並建立只作用於課程專案的 `TWS_AI_Lab` 工作區。

```text
請建置 TWS AI 課程的學員外掛環境。

權威清單：
https://raw.githubusercontent.com/nokiyliao/tws-ai-work-skills/main/learner-setup/plugins.manifest.json

執行規則：
1. 讀取 manifest，處理 plugins 清單中的全部外掛。
2. 明確排除 excluded 清單，不得安裝、啟用或複製這些私人外掛。
3. 檢查每個外掛目前是否已安裝、可用及需要更新；已存在且可用者保留。
4. 缺少的外掛使用其完整 id 安裝或提出官方安裝確認。
5. 清單不包含需要 Google、Microsoft、GitHub 或 Cloudflare 帳號授權的外掛；不得自行加裝替代項目。
6. 不得複製其他電腦的 plugin cache、cookies、token、auth.json 或完整 config.toml。
7. 若安裝後需要重新啟動 ChatGPT，保存待辦清單並告訴我重新啟動；重新啟動後繼續驗證。
8. 最後依序驗證外掛是否可被 Codex 發現，輸出「可使用／需要重啟／安裝失敗」三類結果。
9. 個別外掛失敗時繼續檢查其他項目，最後集中列出失敗原因與人工處理方式。
10. Windows 與 macOS 都必須使用目前使用者帳號的標準 Codex 目錄，不得硬編碼其他作業系統的路徑或指令。
11. 讀取下列學員工作區契約、安裝器與規則檔：
    - https://raw.githubusercontent.com/nokiyliao/tws-ai-work-skills/main/learner-setup/workspace.manifest.json
    - https://raw.githubusercontent.com/nokiyliao/tws-ai-work-skills/main/learner-setup/setup_workspace.py
    - https://raw.githubusercontent.com/nokiyliao/tws-ai-work-skills/main/learner-setup/AGENTS.md
12. 驗證規則檔 SHA-256 符合 workspace manifest，使用目前帳號的 home 建立 `TWS_AI_Lab` 與七個課程子資料夾。
13. 將核准的規則安裝為 `TWS_AI_Lab/AGENTS.md`。這份規則只適用於該課程工作區及其子資料夾，不得寫入 home 根目錄或其他專案。
14. 目標已有不同的 `AGENTS.md` 時保留原檔，停止工作區安裝並回報 `WORKSPACE_POLICY_CONFLICT`；不得靜默覆寫。
15. 執行 `setup_workspace.py check`，只有 digest、七個子資料夾與本機 receipt 全部通過才回報工作區完成。

除安裝清單內的外掛與建立 `TWS_AI_Lab` 外，不要修改我的 Skills、MCP、其他工作資料夾或既有登入設定。
```

## 可能需要學員完成的動作

- macOS 或 Windows 顯示的瀏覽器、桌面控制及檔案存取權限。
- 安裝流程要求的 ChatGPT 重新啟動。

外掛清單不包含任何登入資料、個人工作區或本機快取。
