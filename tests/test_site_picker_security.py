"""Execute the site picker with a DOM that rejects HTML parsing sinks."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_site_picker_treats_names_as_text():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node.js required for the DOM regression')
    template = (Path(__file__).parents[1] / 'maigret/web/templates/base.html').read_text(encoding='utf-8')
    start = template.index('function updateSiteHiddenInput()')
    end = template.index("document.getElementById('settingsModal')", start)
    script = '''
const assert = require('node:assert/strict');
class Element {
    constructor() { this.children = []; this.dataset = {}; this.textContent = ''; }
    set innerHTML(value) { throw new Error('Untrusted name reached an HTML parser'); }
    appendChild(child) { this.children.push(child); }
}
const document = {createElement: () => new Element()};
const payload = '<img src=x onerror=alert(1)>';
const initialSites = [payload];
let selectedSites = new Set(initialSites);
const siteHiddenInput = {};
const selectedSitesContainer = new Element();
'''
    script += template[start:end]
    script += '''
addSite('" onmouseover="alert(2)');
assert.equal(selectedSitesContainer.children.length, 2);
assert.equal(selectedSitesContainer.children[0].textContent, payload);
assert.equal(selectedSitesContainer.children[0].children[0].dataset.site, payload);
'''
    completed = subprocess.run([node, '-e', script], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
