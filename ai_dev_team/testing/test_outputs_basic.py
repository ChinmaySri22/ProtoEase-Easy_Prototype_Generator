import json
import os
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = REPO_ROOT / 'ai_dev_team' / 'outputs'


@pytest.fixture(scope='session')
def artifacts():
    # Require that the pipeline has been run once.
    assert OUTPUTS.exists(), "Run: python -m ai_dev_team.main to generate outputs first."
    files = {p.name: p for p in OUTPUTS.glob('*') if p.is_file()}
    return files


def test_core_files_exist(artifacts):
    assert 'index.html' in artifacts, 'index.html not generated'
    assert 'style.css' in artifacts, 'style.css not generated'
    assert 'script.js' in artifacts, 'script.js not generated'


def test_index_html_is_parseable_and_has_app_root(artifacts):
    html = artifacts['index.html'].read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'lxml')
    assert soup.find('html') is not None, 'HTML root missing'
    assert soup.find(id='app') is not None, 'Expected #app root missing'


def test_metrics_and_qa_logs_if_present(artifacts):
    # Optional but recommended artifacts
    if 'metrics.json' in artifacts:
        data = json.loads(artifacts['metrics.json'].read_text(encoding='utf-8'))
        assert 'latest' in data, 'metrics.json missing latest section'
        latest = data['latest']
        assert isinstance(latest.get('generated_files', []), list)

    if 'qa_log.json' in artifacts:
        qa_data = json.loads(artifacts['qa_log.json'].read_text(encoding='utf-8'))
        assert 'qa' in qa_data and 'timestamp' in qa_data

