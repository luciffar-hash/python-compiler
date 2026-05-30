import streamlit as st
import sys
import io
import multiprocessing

# 核心執行邏輯：用來安全限制執行時間
def execute_user_code(code, queue):
    # 捕捉原本要印到終端機的 print() 內容
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    error_msg = None
    try:
        # 執行程式碼，並使用基礎命名空間做初步安全防護
        exec(code, {"__builtins__": __import__("builtins")}, {})
        stdout_result = redirected_output.getvalue()
    except Exception as e:
        stdout_result = redirected_output.getvalue()
        error_msg = f"❌ 執行出錯：\n{str(e)}"
    finally:
        # 恢復系統標準輸出
        sys.stdout = old_stdout
        
    # 將結果丟回隊列
    queue.put((stdout_result, error_msg))


# 1. 網頁基本設定
st.set_page_config(layout="wide", page_title="Python 線上編異器", page_icon="🐍")

st.title("🇨🇳 Python 線上編譯器")
st.caption("基於 Streamlit 構建的繁體中文學習平台")

# 2. 建立左右分欄版面 (1:1 等寬)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 程式碼編輯區")
    
    # 預設顯示在格子裡的範例程式碼
    default_code = '''# 在這裡編寫 Python 程式碼
print("歡迎使用 Python 線上編譯器！")

# 試試看基礎迴圈
for i in range(1, 4):
    print(f"這是第 {i} 次執行迴圈")
'''
    
    # 讓使用者輸入的大文字框
    user_code = st.text_area(
        label="請輸入 Python 3 程式碼：",
        value=default_code,
        height=400,
        label_visibility="collapsed"
    )
    
    # 綠色的執行按鈕
    run_btn = st.button("▶ 執行程式", type="primary", use_container_width=True)

with col2:
    st.markdown("### 💻 輸出結果 (Terminal)")
    
    # 建立一個動態容器，用來刷新右側的黑底終端機
    output_placeholder = st.empty()
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #888888; padding: 15px; font-family: monospace; min-height: 400px; border-radius: 5px; border: 1px solid #333;">尚未執行程式...</div>',
        unsafe_allow_html=True
    )


# 3. 按下按鈕後的執行邏輯
if run_btn:
    # 基礎安全過濾，防止敏感系統操作
    forbidden_words = ["os.system", "subprocess", "rmdir", "remove", "shutil"]
    if any(word in user_code for word in forbidden_words):
        output_placeholder.markdown(
            '<div style="background-color: #1e1e1e; color: #ff6b6b; padding: 15px; font-family: monospace; min-height: 400px; border-radius: 5px; border: 1px solid #ff6b6b;">⚠️ 系統提示：檢測到敏感程式碼，為了伺服器安全拒絕執行。</div>',
            unsafe_allow_html=True
        )
    else:
        # 使用 multiprocessing（多進程）來跑程式碼，這樣才可以強制設定 3 秒超時
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=execute_user_code, args=(user_code, queue))
        p.start()
        
        # 最多允許跑 3 秒，防止死迴圈（while True）卡死伺服器
        p.join(timeout=3)
        
        if p.is_alive():
            p.terminate()  # 跑太久，強制關閉它
            p.join()
            final_output = "⚠️ 錯誤：程式執行超時（最多 3 秒）！請檢查是否有無窮迴圈。"
        else:
            stdout_res, error_res = queue.get()
            final_output = stdout_res if not error_res else f"{stdout_res}\n{error_res}"
            if not final_output.strip():
                final_output = "（程式執行完畢，無任何輸出結果）"

        # 將最終結果渲染到右側黑底區塊
        output_placeholder.markdown(
            f'<div style="background-color: #1e1e1e; color: #ffffff; padding: 15px; font-family: monospace; min-height: 400px; border-radius: 5px; border: 1px solid #333; white-space: pre-wrap;">{final_output}</div>',
            unsafe_allow_html=True
        )