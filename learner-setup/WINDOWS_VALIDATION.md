# Windows 11 驗收清單

目前狀態：程式與安裝入口已支援 Windows；完整端到端結果仍需在乾淨 Windows 11 帳號確認。

## 建議測試環境

- Windows 11 23H2 或更新版本，x64 或 ARM64。
- 最新版 ChatGPT Windows 桌面應用程式。
- Python 3.10 以上版本，安裝於目前使用者帳號並加入 PATH。
- Microsoft PowerPoint 桌面版；若未安裝，可改用 LibreOffice。
- 可連線 GitHub raw content 與 TWS 唯讀素材服務。

## 端到端驗收

1. 使用沒有既有 `~/.codex/skills` 與 TWS runtime 的一般使用者帳號。
2. 從學習平台複製「課程環境一鍵建置」內容，貼到新的 Codex 任務。
3. 確認 Codex 自動辨識 Windows，且沒有執行 macOS 路徑或指令。
4. 確認 13 個外掛逐項回報「可使用／需要重啟／安裝失敗」，排除清單未被安裝。
5. 確認 Windows Known Folder API 實際回傳的桌面位置下已建立 `TWS_AI_Lab\AGENTS.md`；OneDrive 或公司重新導向有效，digest 與本機 receipt 可通過驗證。
6. 確認 repository manifest 中的全部 Skills 已安裝，沒有複製 cookies、token、auth.json 或其他電腦的設定。
7. 確認 runtime 位於 `%USERPROFILE%\.codex\runtimes\tws-ai`，依賴安裝於隔離環境。
8. 確認 PowerPoint COM 或 LibreOffice 至少一種 renderer 通過。
9. 確認 PPTX 建立、PDF／PNG 渲染、RapidOCR 與遠端素材 digest 驗證全部通過。
10. 重新啟動 ChatGPT 後再次執行 check，結果仍為 PASS。
11. 執行一個 Excel 任務與一個簡報任務，人工開啟成果確認中文字型、圖片、版面及可編輯性。

## 應記錄的失敗類型

- Windows 商店 Python alias 攔截 `python`。
- PowerShell 執行原則阻擋 `.ps1`；Codex 應改用平台中立 Python launcher。
- 公司 Proxy、防毒或群組原則阻擋 GitHub、套件下載、COM 或本機檔案權限。
- ChatGPT Windows 版或學員帳號未提供清單中的外掛。
- PowerPoint 未安裝、未完成首次啟動，或 COM 自動化遭公司原則禁止。
- Windows ARM64 套件輪件、Office 或 ONNX Runtime 相容性問題。

任何一項失敗都應保留精確 blocker，不得將環境標記為完成。
