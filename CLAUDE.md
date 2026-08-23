# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概述

字幕閱讀器（subtitle_reader）是一個 **NVDA 螢幕閱讀器附加元件**，當使用者的焦點停留在瀏覽器的影片播放器內時，從網頁 DOM（透過 NVDA 的 `NVDAObject` 樹）擷取 CC 字幕，並以語音與點字即時報讀。

程式碼只能在 NVDA 的 process 內執行——`ui`、`api`、`globalPluginHandler`、`controlTypes`、`speech`、`gui` 等 import 都由 NVDA 提供。無法在一般 Python 環境中執行或測試，本專案也沒有自動化測試。

## 常用指令

```bash
scons                  # 建置 subtitle_reader-<version>.nvda-addon
scons pot              # 產生 translation template（.pot）
scons -c               # 清除建置產物
scons dev=1            # 建置 dev channel 版本（版號為當日日期）
pre-commit run --all   # CI 執行的檢查（check-ast / check-case-conflict / check-yaml）
ruff check . && ruff format --check .   # pyproject.toml 有完整設定，但未納入 pre-commit
```

建置需求：Python 3.10+、`scons`、`markdown`、`gettext`（msgfmt/xgettext 需在 PATH）。

安裝測試：把產出的 `.nvda-addon` 用 NVDA 安裝，或直接把 `addon/globalPlugins/subtitle_reader/` 複製到 NVDA 的 `scratchpad/globalPlugins/`。除錯用 `NVDA+Ctrl+Z` 開啟 Python Console，`log.debug()` 的輸出可在 NVDA log viewer（`NVDA+F1`）看到（需將 log level 設為 debug）。

## 架構

### 執行流程

1. `GlobalPlugin.event_gainFocus`（`addon/globalPlugins/subtitle_reader/__init__.py`）在每次焦點改變時觸發 `executeSubtitleExtractor()`。
2. `getSubtitleExtractor()` 用**視窗標題**或**網址列的值**去比對每個 extractor 的 `windowTitle` / `url` 正規表達式，挑出對應平台。網址是靠 `findUrl()` 走訪前景視窗物件樹找出網址列元件（有 per-`windowHandle` 快取）。
3. 選中的 extractor 依序呼叫 `getVideoPlayer()` → `getSubtitleContainer()`，任一步回傳 falsy 就中止（視為此頁面沒有可讀字幕）。
4. 兩者都找到後，啟動 `wx` 的 `NonReEntrantTimer`，以約每 0.1 秒的節奏持續呼叫 `readSubtitle()` → `extractor.onReadingSubtitle()` + `extractor.getSubtitle()`。
5. `processSubtitle()` 做去重：以 ` | ` 為分隔符切開字幕片段，過濾掉與前一次重疊的部分，只把「新增的內容」交給 `ui.message()`。這是本專案最微妙的邏輯——各平台字幕是逐字/逐句累加出現的，直接報讀會嚴重重複。

因為 NVDAObject 的存取隨時可能因頁面重繪而失效，走訪物件樹的程式碼幾乎都必須捕捉 `COMError` 與 `RuntimeError`。

### 新增平台支援

每個平台是 `subtitleExtractors/` 下的一個模組，內含一個 `SubtitleExtractor` 子類別。**不需要註冊**：`SubtitleExtractor.initialize()` 用 `pkgutil.iter_modules` 匯入資料夾內所有模組，而 `__init_subclass__` 會自動把子類別加進 `SubtitleExtractor.extractors`（「支援影音平台」選單也是由這個列表產生）。

子類別需提供：

- `info`：`{'name', 'url', 'status'}`，`status` 用 `SupportStatus.supported` / `SupportStatus.invalid`。
- `windowTitle` 或 `url` 正規表達式（擇一；優先用 `windowTitle`，因為部分瀏覽器取不到網址）。
- `getVideoPlayer()` / `getSubtitleContainer()`：通常用 `object_finder.find(obj, nextAttr, attrName, attrValue)` 沿著 `parent` / `next` / `firstChild` 方向找特定 `id`、`class` 或 `role`。`find` 會同時查物件屬性與 `IA2Attributes`；`class` 用子字串比對，`attrValue` 傳 list 表示任一符合。
- 選用：`getSubtitle(obj)` 覆寫（預設實作沿 `.next` 串接子物件的 `name`，以 ` | \r\n` 連接）、`onReadingSubtitle()`（每次輪詢的額外工作，如 YouTube 聊天室）、`terminate()`（取消非同步搜尋）。

**瀏覽器差異**：base class 提供 `<appName>GetSubtitleContainer()` / `<appName>GetSubtitle()` 的 dispatch 慣例，`msedge`/`brave`/`browser`(Yandex) 預設轉呼叫 `chrome*` 版本。當 Chrome 與 Firefox 的 DOM 結構不同時，在 `getSubtitleContainer()` 內用 `getattr(self, appName + 'GetSubtitleContainer')()` 分流（見 `netflix.py`）。

**role 相容性**：一律用 `compatible.role('grouping')` 而非直接引用 `controlTypes`——NVDA 2021.2 前後常數命名不同。

**非同步搜尋**：需要在大量物件中掃描（如 YouTube 聊天室）時用 `object_finder.search()`，它會切成每 20ms 一段並用 `core.callLater` 讓出主執行緒，避免卡住 NVDA。務必在 `terminate()` 中 `cancel()` 這些搜尋物件。

詳細的手把手教學見 `addon/doc/en/developer-guide.md`（另有 zh_TW / zh_HK 版本）。

### 其他模組

- `config.py`：`conf` 是一個 dict 子類別，載入/寫入 `<NVDA configPath>/subtitle_reader.json`；新增設定項要同時補上預設值、`gui.py` 的選單項、`__init__.py` 的 toggle handler 與 `initMenu()` 中的 `Check()`。
- `gui.py`：NVDA 工具選單下的整個選單樹，以及更新對話框。
- `update.py`：自動/手動更新檢查，直接抓 GitHub raw 上的 `main` 分支內容比對版本。
- `sound.py` + `pybass/`：BASS 音效函式庫綁定，用於播放 `assets/sounds/` 的提示音與更新時的背景音樂。
- `potPlayer.py`：特例——透過 monkey-patch `speech.processText` 與 `winInputHook.keyDownCallback` 支援 PotPlayer 桌面播放器，不走 extractor 機制。

## 慣例

- **縮排用 tab**（`ruff format` 設定為 `indent-style = "tab"`），line-length 110。
- 使用者可見字串一律包在 `_()` 中，並在前一行加上 `# Translators: ...` 註解；`buildVars.py` 中的字串也會被抽取。base language 是 `zh_TW`，翻譯放在 `addon/locale/<lang>/LC_MESSAGES/nvda.po`。
- 註解與 commit 訊息使用繁體中文（部分較舊或外部貢獻的檔案有法文/英文註解）。
- **版本號規則**（`buildVars.py` 的 `addon_version`）：修 bug 或調整功能 → 小數點後第二位 +1；新增影音平台支援 → 小數點後第一位 +1 且第二位歸零。小數點後為 0 也不可省略（附加元件商店以整數比較）。
- `changelog.md`（根目錄）是下一個 release 的說明內容，會被 CI 直接當作 GitHub Release body；`addon/doc/*/changelog.md` 則是隨附在附加元件內的歷史紀錄。
- `addon/manifest.ini`、`*.html`、`*.mo`、`*.pot`、`.nvda-addon` 都是建置產物且列在 `.gitignore`——**不要手動編輯**，改 `buildVars.py`、`manifest.ini.tpl` 或對應的 `.md` / `.po`。
