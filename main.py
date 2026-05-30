import streamlit as st
import sys
import io
import multiprocessing
# 💡 引入專業的彩色程式碼編輯器套件
from code_editor import code_editor

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
st.caption("基於 Streamlit 構建的繁體中文學習平台")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 程式碼編輯區")
    
    default_code = '''# 在這裡編寫 Python 程式碼
print("歡迎使用 Python 線上編譯器！")

# 試試看基礎迴圈
for i in range(1, 4):
    print(f"這是第 {i} 次執行迴圈")
'''
    
    # 💡 這裡原本是 st.text_area，現在改用專業的 code_editor
    # theme="monokai" 會讓它呈現經典的黑底彩色代碼風格
    response = code_editor(
        default_code,
        lang="python",
        theme="monokai",
        height=[20, 25], # 限制高度
        options={"fontSize": 16}
    )
    
    # 從編輯器元件中單獨把文字撈出來
    user_code = response['text']
    
    run_btn = st.button("▶ 執行程式", type="primary", use_container_width=True)

with col2:
    st.markdown("### 💻 輸出結果 (Terminal)")
    
    output_placeholder = st.empty()
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #888888; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">尚未執行程式...</div>',
        unsafe_allow_html=True
    )

if run_btn:
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
