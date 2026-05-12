"""Web UI strings and API error messages (en / zh)."""

from __future__ import annotations

from typing import Literal

Language = Literal["en", "zh"]

_UI_EN: dict[str, str] = {
    "title": "Whiteboard",
    "urlPlaceholder": "Page URL",
    "openWeb": "Open URL",
    "enterHtml": "Edit Page",
    "collapse": "Collapse",
    "moreMenu": "More",
    "history": "History",
    "downloadPdf": "Print / PDF",
    "settings": "Settings",
    "htmlPlaceholder": "Paste HTML or Markdown (multi-line; full HTML documents allowed)",
    "updateHtml": "Apply",
    "clear": "Clear",
    "historyTitle": "History",
    "close": "Close",
    "closeAria": "Close",
    "loading": "Loading…",
    "historyEmpty": "No history yet",
    "historyLoadError": "Could not load history",
    "restoreFailed": "Restore failed",
    "enterContent": "Please enter content",
    "updateFailed": "Update failed",
    "pdfOnlyHtml": "Available when the board shows HTML or Markdown content",
    "saveMarkdown": "Save as Markdown",
    "saveHtmlExport": "Save as HTML",
    "saveOnlyMarkdown": "Available only when the board shows Markdown content",
    "pickMarkdownFile": "Choose file…",
    "fileTooLarge": "File is too large (max 2 MB)",
    "historyTypeUrl": "URL",
    "historyTypeHtml": "HTML",
    "historyTypeMarkdown": "Markdown",
    "historyEdit": "Edit",
    "historyCancelEdit": "Cancel edit",
    "historyDeleteSelected": "Delete",
    "historyDeleteConfirm": "Delete {count} selected item(s)? This cannot be undone.",
    "historyDeleteFailed": "Could not delete history",
    "historyDeletePartial": "{failed} item(s) could not be deleted.",
    "historySelectEntry": "Select",
    "settingsTitle": "Settings",
    "languageLabel": "Language",
    "langEnglish": "English",
    "langChinese": "中文",
    "applyLanguage": "Save",
    "cancel": "Cancel",
    "dateLocale": "en-US",
}

_UI_ZH: dict[str, str] = {
    "title": "白板服务",
    "urlPlaceholder": "输入网页 URL",
    "openWeb": "打开 URL",
    "enterHtml": "编辑页面",
    "collapse": "收起",
    "moreMenu": "更多",
    "history": "历史页面",
    "downloadPdf": "下载为 PDF",
    "settings": "设置",
    "htmlPlaceholder": "粘贴 HTML 或 Markdown（支持多行、完整 HTML 页面）",
    "updateHtml": "应用",
    "clear": "清空",
    "historyTitle": "历史页面",
    "close": "关闭",
    "closeAria": "关闭",
    "loading": "加载中…",
    "historyEmpty": "暂无历史记录",
    "historyLoadError": "加载失败",
    "restoreFailed": "恢复失败",
    "enterContent": "请输入内容",
    "updateFailed": "更新失败",
    "pdfOnlyHtml": "在使用 HTML 或 Markdown 内容时可导出",
    "saveMarkdown": "保存为 Markdown",
    "saveHtmlExport": "保存为 HTML",
    "saveOnlyMarkdown": "仅在使用 Markdown 内容时可保存",
    "pickMarkdownFile": "选择文件…",
    "fileTooLarge": "文件过大（最大 2 MB）",
    "historyTypeUrl": "网页",
    "historyTypeHtml": "HTML",
    "historyTypeMarkdown": "Markdown",
    "historyEdit": "编辑",
    "historyCancelEdit": "取消编辑",
    "historyDeleteSelected": "删除",
    "historyDeleteConfirm": "确定删除已选中的 {count} 条记录？此操作不可撤销。",
    "historyDeleteFailed": "删除失败",
    "historyDeletePartial": "有 {failed} 条未能删除。",
    "historySelectEntry": "选择",
    "settingsTitle": "设置",
    "languageLabel": "语言",
    "langEnglish": "English",
    "langChinese": "中文",
    "applyLanguage": "保存",
    "cancel": "取消",
    "dateLocale": "zh-CN",
}

_API_EN = {
    "history_not_found": "Record not found or file missing.",
    "history_invalid_type": "Invalid record type.",
    "history_html_missing": "Not an HTML record or file missing.",
    "history_md_missing": "Not a Markdown record or file missing.",
}

_API_ZH = {
    "history_not_found": "记录不存在或文件缺失",
    "history_invalid_type": "无效的记录类型",
    "history_html_missing": "不是 HTML 记录或文件不存在",
    "history_md_missing": "不是 Markdown 记录或文件不存在",
}


def ui_strings_for(lang: Language) -> dict[str, str]:
    base = _UI_EN if lang != "zh" else _UI_ZH
    return dict(base)


def api_detail(lang: Language, key: str) -> str:
    table = _API_ZH if lang == "zh" else _API_EN
    return table.get(key, _API_EN.get(key, key))
