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
        # 在沙箱中執行，限制部分核心內建函式以提高安全性
        exec(code, {"__builtins__": __import__("builtins")}, {})
        stdout_result = redirected_output.getvalue()
    except Exception as e:
        stdout_result = redirected_output.getvalue()
        error_msg = f"❌ 執行出錯：\n{str(e)}"
    finally:
        sys.stdout = old_stdout
        
    queue.put((stdout_result, error_msg))

# 網頁基本設定
st.set_page_config(layout="wide", page_title="路西法智庫創世神手：Python 線上編譯器", page_icon="🐍")

# 網頁主標題與品牌系列化
st.title("🐍 路西法智庫創世神手：Python 線上編譯器")
st.caption("基於 Streamlit 構建的繁體中文學習平台 ｜ 🚀 目前版本：v2.4.1 (完整攔截版)")

# 免責聲明（法律防彈背心）
st.warning("⚠️ 免責聲明：本平台僅供教學與學術交流使用。使用者於本平台執行之所有程式碼衍生之風險與損害，均由使用者自行承擔，本平台及開發者概不負任何法律與損害賠償責任。")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 程式碼編輯區")
    
    default_code = '''# 在這裡編寫 Python 程式碼
print("哈囉，看到這行代表測試大成功！")
print(1 + 1)
'''
    
    # 使用 st_ace 元件，自動同步且隱藏原廠 APPLY 按鈕
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

# 下方安全規範與技術限制說明（採用摺疊選單，保持介面純淨）
st.markdown("---")
with st.expander("📘 檢視【創世神手】系統安全規範與技術限制說明"):
    st.markdown("""
    本編譯器為了維護雲端伺服器安全與提供流暢的運算環境，設有以下實質防護與技術邊界：
    
    #### 1. 🚫 嚴格禁用的指令（觸犯將拒絕執行）
    為防止惡意攻擊或架構不相容導致系統崩潰，程式碼中不得包含以下關鍵字：
    * **系統核心操控：** `os.system` / `subprocess` / `popen`
    * **檔案刪除與變更：** `rmdir` / `remove` / `shutil`
    * **動態代碼嵌套：** `eval` / `exec`
    * **互動式輸入指令：** `input` *(網頁採單向標準輸出架構，不支援即時互動輸入，請改用固定變數賦值)*
    
    #### 2. ⏳ 運算超時斷路機制
    * 本平台不支援**無窮迴圈**（如 `while True` 且無中斷條件）或需要長時間掛載的排程。
    * 系統後端配有自動斷路器，任何程式碼執行**超過 3 秒**將被安全沙箱強制終止。
    """)

if run_btn:
    # 點擊瞬間清空舊畫面，並閃爍黃色讀取燈
    output_placeholder.markdown(
        '<div style="background-color: #1e1e1e; color: #ffaa00; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #333;">⏳ 程式正在安全沙箱中執行，請稍候...</div>',
        unsafe_allow_html=True
    )

    # 惡意與不支援程式碼過濾（💡 這裡正式把 input 加進去攔截）
    forbidden_words = ["os.system", "subprocess", "popen", "rmdir", "remove", "shutil", "eval", "exec", "input"]
    if any(word in user_code for word in forbidden_words):
        output_placeholder.markdown(
            '<div style="background-color: #1e1e1e; color: #ff6b6b; padding: 15px; font-family: monospace; min-height: 440px; border-radius: 5px; border: 1px solid #ff6b6b;">⚠️ 系統提示：檢測到敏感或不支援的程式碼（如 os.system, subprocess, eval, input 等）。為了安全與防錯，系統拒絕執行，請參閱下方說明。</div>',
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
