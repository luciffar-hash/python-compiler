import streamlit as st
import sys
import io
import multiprocessing
# 引入專業的彩色程式碼編輯器套件
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
    
    # 彩色編輯器元件設定
    response = code_editor(
        default_code,
        lang="python",
        theme="monokai",
        height=[20, 25], 
        options={"fontSize": 16}
    )
    
    user_code = response['text']
    
    run_btn = st.button("▶ 執行程式", type="primary", use_container_width=True)

with col2:
    st.markdown("### 💻 輸出結果 (Terminal)")
    
    output_placeholder = st.empty()
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #888888; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">環境就緒，等待執行程式...</div>',
        unsafe_allow_html=True
    )

# 當按下執行按鈕時的邏輯
if run_btn:
    # ✨ 核心優化：按下的瞬間，立刻清空舊的「100」，並顯示正在執行的黃色提示
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #ffaa00; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">⏳ 程式正在安全沙箱中執行，請稍候...</div>',
        unsafe_allow_html=True
    )

    # 惡意程式碼過濾機制
    forbidden_words = ["os.system", "subprocess", "rmdir", "remove", "shutil"]
    if any(word in user_code for word in forbidden_words):
        output_placeholder.markdown(
            '<div style="background-color: #1e1e1e; color: #ff6b6b; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #ff6b6b;">⚠️ 系統提示：檢測到敏感程式碼，為了伺服器安全拒絕執行。</div>',
            unsafe_allow_html=True
        )
    else:
        # 使用多進程跑沙箱安全機制
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=execute_user_code, args=(user_code, queue))
        p.start()
        
        # 最高死線限制為 3 秒
        p.join(timeout=3)
        
        # 如果 3 秒到了還在跑，代表遇到了死迴圈
        if p.is_alive():
            p.terminate()
            p.join()
            final_output = "⚠️ 錯誤：程式執行超時（最多 3 秒）！請檢查是否有無窮迴圈。"
        else:
            stdout_res, error_res = queue.get()
            final_output = stdout_res if not error_res else f"{stdout_res}\n{error_res}"
            if not final_output.strip():
                final_output = "（程式執行完畢，無任何輸出結果）"

        # 最終將結果（成功或超時）渲染到 Terminal 上
        output_placeholder.markdown(
            f'<div style="background-color: #1e1e1e; color: #ffffff; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333; white-space: pre-wrap;">{final_output}</div>',
            unsafe_allow_html=True
        )
