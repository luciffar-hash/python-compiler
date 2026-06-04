import streamlit as st
import sys
import io
import multiprocessing
import ast
from streamlit_ace import st_ace

# 網頁基本設定
st.set_page_config(layout="wide", page_title="路西法智庫創世神手：Python 線上編譯器", page_icon="🐍")

# 頁面頂端資訊
st.title("🐍 路西法智庫創世神手：Python 線上編譯器")
st.subheader("🚀 版本：v2.4.4")
st.caption("基於 Streamlit 構建的繁體中文學習平台 ｜ 採用 AST 智慧過濾技術")

# 初始化 session_state
if 'code_content' not in st.session_state:
    st.session_state.code_content = '''# 在這裡編寫 Python 程式碼
print("哈囉，看到這行代表測試大成功！")
print(1 + 1)
'''

def execute_user_code(code, queue):
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    error_msg = None
    try:
        exec(code, {"__builtins__": __import__("builtins")}, {})
        stdout_result = redirected_output.getvalue()
    except Exception as e:
        stdout_result = redirected_output.getvalue()
        error_msg = f"❌ 執行出錯：\n{str(e)}"
    finally:
        sys.stdout = old_stdout
        
    queue.put((stdout_result, error_msg))

def is_code_safe(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False, "語法錯誤，請檢查程式碼。"

    forbidden_calls = {'eval', 'exec', 'input'}
    forbidden_imports = {'os', 'subprocess', 'shutil'}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                return False, f"偵測到禁止使用的函數: {node.func.id}"
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name in forbidden_imports:
                    return False, f"偵測到禁止導入的模組: {n.name}"
        if isinstance(node, ast.ImportFrom):
            if node.module in forbidden_imports:
                return False, f"偵測到禁止導入的模組: {node.module}"
                
    return True, ""

st.warning("⚠️ 免責聲明：本平台僅供教學與學術交流使用。")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 程式碼編輯區")
    
    # 編輯器內容綁定到 session_state
    st.session_state.code_content = st_ace(
        value=st.session_state.code_content, 
        language="python", theme="monokai",
        font_size=16, tab_size=4, height=400, 
        auto_update=True, key="python_editor"
    )
    
    # 按鈕區塊
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        run_btn = st.button("▶ 執行程式", type="primary", use_container_width=True)
    with btn_col2:
        if st.button("🗑 清除編輯區", use_container_width=True):
            st.session_state.code_content = ""
            st.rerun()

with col2:
    st.markdown("### 💻 輸出結果 (Terminal)")
    output_placeholder = st.empty()
    output_placeholder.markdown('<div style="background-color: #1e1e1e; color: #888888; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">環境就緒，等待執行程式...</div>', unsafe_allow_html=True)

st.markdown("---")
with st.expander("📘 檢視【創世神手】系統安全規範"):
    st.markdown("已升級為 AST 分析，並支援清空編輯區功能。")

if run_btn:
    output_placeholder.markdown('<div style="background-color: #1e1e1e; color: #ffaa00; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">⏳ 執行中...</div>', unsafe_allow_html=True)
    
    is_safe, error_msg = is_code_safe(st.session_state.code_content)
    
    if not is_safe:
        output_placeholder.markdown(f'<div style="background-color: #1e1e1e; color: #ff6b6b; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #ff6b6b;">⚠️ 系統提示：{error_msg}</div>', unsafe_allow_html=True)
    else:
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=execute_user_code, args=(st.session_state.code_content, queue))
        p.start()
        p.join(timeout=3)
        
        if p.is_alive():
            p.terminate()
            p.join()
            final_output = "⚠️ 錯誤：程式執行超時（3 秒限制）！"
        else:
            stdout_res, err_res = queue.get()
            final_output = stdout_res if not err_res else f"{stdout_res}\n{err_res}"
            if not final_output.strip(): final_output = "（程式執行完畢，無輸出）"

        output_placeholder.markdown(f'<div style="background-color: #1e1e1e; color: #ffffff; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333; white-space: pre-wrap;">{final_output}</div>', unsafe_allow_html=True)
