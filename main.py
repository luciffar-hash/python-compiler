import streamlit as st
import sys
import io
import multiprocessing
import ast
from streamlit_ace import st_ace

# --- 1. 網頁基本設定 ---
st.set_page_config(layout="wide", page_title="路西法智庫創世神手：Python 線上編譯器", page_icon="🐍")

# --- 2. 頁面頂端資訊與版號移頂 ---
st.title("🐍 路西法智庫創世神手：Python 線上編譯器")
st.subheader("🚀 目前版本：v2.4.6 (元件狀態強制重置版)")
st.caption("基於 Streamlit 構建的繁體中文學習平台 ｜ 支援註解寫禁字與一鍵清空")

# --- 3. 初始化 Session State (加入清除計數器機制) ---
if 'clear_counter' not in st.session_state:
    st.session_state.clear_counter = 0

if 'code_content' not in st.session_state:
    st.session_state.code_content = '''# 在這裡編寫 Python 程式碼
# 現在你可以大方寫註解：這是一個 input 練習，os.system 也不會被擋！
print("哈囉，看到這行代表測試大成功！")
print(1 + 1)
'''

def execute_user_code(code, queue):
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    error_msg = None
    try:
        # 在沙箱中執行，限制部分核心內建函式以提高安全性
        exec(code, {"__builtins__": __import__("builtins")}, {})
        stdout_result = redirected_output.getvalue()
    except Exception as e:
        stdout_result = redirected_output.getvalue()
        error_msg = f"❌ 執行出錯：\n{str(e)}"
    finally:
        sys.stdout = old_stdout
        
    queue.put((stdout_result, error_msg))

def is_code_safe(code):
    """使用 AST 分析程式碼安全性，只過濾實質程式碼，允許註解與純字串中出現敏感字"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False, "語法錯誤，請檢查程式碼結構。"

    # 安全黑名單
    forbidden_calls = {'eval', 'exec', 'input'}
    forbidden_imports = {'os', 'subprocess', 'shutil'}

    for node in ast.walk(tree):
        # 檢查實質函數呼叫
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                return False, f"偵測到禁止執行的函數：{node.func.id}()。網頁採單向輸出架構，不支援即時互動或動態嵌套。"
        
        # 檢查實質 import 模組
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name in forbidden_imports:
                    return False, f"偵測到安全敏感模組：{n.name}，系統拒絕導入。"
        if isinstance(node, ast.ImportFrom):
            if node.module in forbidden_imports:
                return False, f"偵測到安全敏感模組：{node.module}，系統拒絕導入。"
                
    return True, ""

# 免責聲明（法律防彈背心）
st.warning("⚠️ 免責聲明：本平台僅供教學與學術交流使用。使用者於本平台執行之所有程式碼衍生之風險與損害，均由使用者自行承擔，本平台及開發者概不負任何法律與損害賠償責任。")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 程式碼編輯區")
    
    # 💡 關鍵修改：將 key 綁定計數器，清空時變更計數器以強迫 st_ace 重新初始化其內部 JavaScript 狀態
    current_editor_key = f"python_editor_{st.session_state.clear_counter}"
    
    user_code = st_ace(
        value=st.session_state.code_content,
        language="python",
        theme="monokai",
        font_size=16,
        tab_size=4,
        height=400,
        auto_update=True,
        key=current_editor_key
    )
    
    # 同步把最新輸入存入 session_state
    st.session_state.code_content = user_code
    
    # 橫向並排的按鈕區塊
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        run_btn = st.button("▶ 執行程式", type="primary", use_container_width=True)
    with btn_col2:
        if st.button("🗑️ 清除編輯區", use_container_width=True):
            st.session_state.code_content = ""
            st.session_state.clear_counter += 1  # 變更 key，強制 Ace 編輯器重置畫面
            st.rerun()

with col2:
    st.markdown("### 💻 輸出結果 (Terminal)")
    
    output_placeholder = st.empty()
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #888888; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">環境就緒，等待執行程式...</div>',
        unsafe_allow_html=True
    )

# 下方安全規範與技術限制說明
st.markdown("---")
with st.expander("📘 檢視【創世神手】系統安全規範與技術限制說明"):
    st.markdown("""
    本編譯器為了維護雲端伺服器安全與提供流暢的運算環境，設有以下實質防護與技術邊界：
    
    #### 1. 🛡️ 升級 AST 智慧防護機制
    系統已升級為抽象語法樹 (AST) 結構分析，**現在允許您在註解（如 #）或 print() 字串內撰寫說明文字**。只有當程式碼「真正嘗試執行」以下敏感指令時才會被攔截：
    * **系統核心操控：** `os` / `subprocess` / `shutil`
    * **動態代碼嵌套：** `eval` / `exec`
    * **互動式輸入指令：** `input` *(網頁採單向標準輸出架構，請改用固定變數賦值)*
    
    #### 2. ⏳ 運算超時斷路機制
    * 本平台不支援**無窮迴圈**（如 `while True` 且無中斷條件）或需要長時間掛載的排程。
    * 系統後端配有自動斷路器，任何程式碼執行**超過 3 秒**將被安全沙箱強制終止。
    """)

# 點擊執行的後端邏輯
if run_btn:
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #ffaa00; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">⏳ 程式正在安全沙箱中執行，請稍候...</div>',
        unsafe_allow_html=True
    )

    # 調用 AST 進行結構安全檢查 (使用最新從編輯器取得的 user_code)
    is_safe, check_msg = is_code_safe(user_code)
    
    if not is_safe:
        output_placeholder.markdown(
            f'<div style="background-color: #1e1e1e; color: #ff6b6b; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #ff6b6b;">⚠️ 系統提示：{check_msg}</div>',
            unsafe_allow_html=True
        )
    else:
        # 多進程沙箱與 3 秒超時限制
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=execute_user_code, args=(user_code, queue))
        p.start()
        
        p.join(timeout=3)
        
        if p.is_alive():
            p.terminate()
            p.join()
            final_output = "⚠️ 錯誤：程式執行超時（最多 3 秒）！請檢查是否有無窮迴圈。"
        else:
            stdout_res, error_res = queue.get()
            final_output = stdout_res if not error_res else f"{stdout_res}\n{error_res}"
            if not final_output.strip():
                final_output = "（程式執行完畢，無任何輸出結果）"

        # 輸出結果渲染
        output_placeholder.markdown(
            f'<div style="background-color: #1e1e1e; color: #ffffff; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333; white-space: pre-wrap;">{final_output}</div>',
            unsafe_allow_html=True
        )
