"""Readable club tables: first numeric-header click always sorts highest first."""
import json
from pathlib import Path
import streamlit.components.v1 as components
from mfl_text import read_font_url

def table_html(frame,sort_by=None):
    columns=[str(c) for c in frame.columns]
    numeric=[str(c) for c in frame.select_dtypes(include='number').columns]
    if sort_by is None:sort_by=next((c for c in ('OVR ↑','OVR change','ovr_gain') if c in columns),numeric[0] if numeric else columns[0])
    payload={'columns':columns,'numeric':numeric,'sortBy':sort_by,'rows':json.loads(frame.to_json(orient='records'))}
    return Path(__file__).with_name('ranked_table.html').read_text().replace('/*TABLE_DATA*/',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')).replace('READ_FONT_URL',read_font_url()).replace('BOLD_FONT_URL',read_font_url(True))

def render(frame,sort_by=None,height=500,**kwargs):
    components.html(table_html(frame,sort_by),height=height,scrolling=True)
