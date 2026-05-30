import streamlit as st
import sys
import io
import multiprocessing
# 引入穩定的專業彩色編輯器套件
from streamlit_ace import st_ace

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

# 網頁基本設定
st.set_page_config(layout="wide", page_title="Python 線上編譯器", page_icon="🐍")

st.title("🇨🇳 Python 線上編譯器")
# 💡 升級版本號至 v2.2.0
st.caption("基於 Streamlit 構建的繁體中文學習平台 ｜ 🚀 目前版本：v2.2.0 (無按鈕純淨版)")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 程式碼編輯區")
    
    default_code = '''# 在這裡編寫 Python 程式碼
print("哈囉，看到這行代表測試大成功！")
print(1 + 1)
'''
    
    # 使用 st_ace 元件
    # 💡 關鍵加入 auto_update=True，直接讓底層的 APPLY 紅色按鈕消失！
    user_code = st_ace(
        value=default_code,
        language="python",
        theme="monokai",
        font_size=16,
        tab_size=4,
        height=400,
        auto_update=True,
        key="python_editor"
    )
    
    # 唯一核心執行鈕：統一使用滑鼠點擊執行
    run_btn = st.button("▶ 執行程式", type="primary", use_container_width=True)

with col2:
    st.markdown("### 💻 輸出結果 (Terminal)")
    
    output_placeholder = st.empty()
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #888888; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">環境就緒，等待執行程式...</div>',
        unsafe_allow_html=True
    )

if run_btn:
    # 點擊瞬間清空畫面並閃黃燈
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #ffaa00; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">⏳ 程式正在安全沙箱中執行，請稍候...</div>',
        unsafe_allow_html=True
    )

    forbidden_words = ["os.system", "subprocess", "rmdir", "remove", "shutil"]
    if any(word in user_code for word in forbidden_words):
        output_placeholder.markdown(
            '<div style="background-color: #1e1e1e; color: #ff6b6b; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #ff6b6b;">⚠️ 系統提示：檢測到敏感程式碼，為了伺服器安全拒絕執行。</div>',
            unsafe_allow_html=True
        )
    else:
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

        output_placeholder.markdown(
            f'<div style="background-color: #1e1e1e; color: #ffffff; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333; white-space: pre-wrap;">{final_output}</div>',
            unsafe_allow_html=True
        )
