# TWS AI 課程外掛建置 Prompt

將以下內容貼到新的 Codex 任務。Codex 會依 manifest 檢查 13 個不需外部帳號登入的外掛，安裝或啟用缺少項目。

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

不要修改我的 Skills、MCP、工作資料夾或既有登入設定。
```

## 可能需要學員完成的動作

- macOS 或 Windows 顯示的瀏覽器、桌面控制及檔案存取權限。
- 安裝流程要求的 ChatGPT 重新啟動。

外掛清單不包含任何登入資料、個人工作區或本機快取。
