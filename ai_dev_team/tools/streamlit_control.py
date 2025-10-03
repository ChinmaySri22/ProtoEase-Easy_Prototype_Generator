import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import find_dotenv, load_dotenv, set_key


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = REPO_ROOT / 'ai_dev_team' / 'outputs'
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def is_valid_hex_color(value: str) -> bool:
    return bool(re.fullmatch(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})", value.strip()))


def read_existing_user_request() -> str:
    load_dotenv()
    env_path = find_dotenv(usecwd=True) or str(REPO_ROOT / '.env')
    env_file = Path(env_path)
    if env_file.exists():
        # Fallback manual read to show in UI without parsing all keys
        try:
            for line in env_file.read_text(encoding='utf-8').splitlines():
                if line.startswith('USER_PRODUCT_REQUEST='):
                    return line.split('=', 1)[1].strip().strip('"')
        except Exception:
            pass
    return ''


def save_user_product_request(request_str: str) -> None:
    env_path = find_dotenv(usecwd=True) or str(REPO_ROOT / '.env')
    if not env_path:
        env_path = str(REPO_ROOT / '.env')

    # Backup existing value
    prev = read_existing_user_request()
    if prev:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = OUTPUTS_DIR / f'user_product_request_{timestamp}.txt'
        backup_path.write_text(prev, encoding='utf-8')

    # Ensure .env exists
    env_file = Path(env_path)
    if not env_file.exists():
        env_file.write_text('', encoding='utf-8')

    # Write key safely
    set_key(env_path, 'USER_PRODUCT_REQUEST', request_str)


def main() -> None:
    st.set_page_config(page_title='Generator Control', page_icon='🧩', layout='centered')

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        html, body, [class*="css"]  {
            font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        }
        .stButton>button { font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title('Plain-English → Runnable Frontend Prototype')
    st.caption('Enter any product request (free-form). Optional fields can enrich or constrain the output.')

    with st.form('control_form'):
        base_request = st.text_area(
            'Product Request (required)',
            value='Create a modern single-page web app. Describe features, tech constraints, and output expectations.',
            height=140,
            help='Describe what you want built. You can request any app (not limited to to-do).',
        )
        app_name = st.text_input('App Name (optional)', value='')
        accent_color = st.color_picker('Accent Color (optional)', value='#4F46E5')
        extra_feature = st.selectbox(
            'Extra Feature',
            ['None', 'Due dates', 'Priority tags', 'Reorder by drag'],
            index=0,
        )
        tone = st.text_input('Target Audience / Tone (optional)', value='')

        submitted = st.form_submit_button('Save & Update')

    if submitted:
        if not base_request.strip():
            st.error('Please enter a Product Request.')
            return
        if accent_color and not is_valid_hex_color(accent_color):
            st.error('Accent Color must be a valid hex code like #4F46E5.')
            return

        parts = [base_request.strip()]
        if app_name:
            parts.append(f"App name: {app_name}.")
        if accent_color:
            parts.append(f"Accent color: {accent_color}.")
        if extra_feature and extra_feature != 'None':
            parts.append(f"Extra feature: {extra_feature}.")
        if tone:
            parts.append(f"Tone: {tone}.")

        composed = ' '.join(parts)

        try:
            save_user_product_request(composed)
            st.success('USER_PRODUCT_REQUEST saved to .env')
            st.code(composed)
            st.info('You can now start generation below.')
        except Exception as e:
            # Fallback write into outputs dir
            fallback_path = OUTPUTS_DIR / 'user_product_request.txt'
            fallback_path.write_text(composed, encoding='utf-8')
            st.warning('Saved to ai_dev_team/outputs/user_product_request.txt due to .env write issue.')
            st.exception(e)

    # Show existing value (read-only)
    existing = read_existing_user_request()
    if existing:
        with st.expander('Current USER_PRODUCT_REQUEST (.env)'):
            st.code(existing)

    st.divider()
    st.subheader('Generate Prototype')
    st.caption('Runs the pipeline and streams logs here; results are saved to ai_dev_team/outputs/.')

    if st.button('Start Generation', type='primary'):
        log_area = st.empty()
        with st.status('Running pipeline...', expanded=True) as status:
            try:
                cmd = [sys.executable, '-m', 'ai_dev_team.main']
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(REPO_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                lines = []
                for line in proc.stdout:
                    lines.append(line.rstrip('\n'))
                    # Render last ~200 lines to keep UI snappy
                    log_area.code('\n'.join(lines[-200:]))
                ret = proc.wait()
                if ret == 0:
                    status.update(label='Pipeline completed', state='complete')
                else:
                    status.update(label=f'Pipeline exited with code {ret}', state='error')
            except Exception as e:
                status.update(label='Pipeline failed to start', state='error')
                st.exception(e)

        # After run, show quick links if exist
        outputs = {
            'PRD.md': OUTPUTS_DIR / 'PRD.md',
            'file_breakdown.json': OUTPUTS_DIR / 'file_breakdown.json',
            'index.html': OUTPUTS_DIR / 'index.html',
            'style.css': OUTPUTS_DIR / 'style.css',
            'script.js': OUTPUTS_DIR / 'script.js',
            'qa_log.json': OUTPUTS_DIR / 'qa_log.json',
            '_debug_raw_coder_output.txt': OUTPUTS_DIR / '_debug_raw_coder_output.txt',
            '_debug_errors.txt': OUTPUTS_DIR / '_debug_errors.txt',
        }
        available = {name: p for name, p in outputs.items() if p.exists()}
        if available:
            st.success('Artifacts generated:')
            cols = st.columns(2)
            i = 0
            for name, path in available.items():
                with cols[i % 2]:
                    st.write(name)
                    try:
                        st.download_button(
                            label=f'Download {name}',
                            data=path.read_bytes(),
                            file_name=name,
                        )
                    except Exception:
                        st.write(str(path))
                i += 1
        else:
            st.warning('No artifacts found. Check debug logs above.')


if __name__ == '__main__':
    main()


