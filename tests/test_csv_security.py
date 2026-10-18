import csv
from io import StringIO

import pytest
from maigret.report import generate_csv_report


@pytest.mark.parametrize('value', ['=1+1', '+1+1', '-1+1', '@SUM(1)', '\t=1+1', '\r=1+1', '  =1+1'])
def test_csv_exports_untrusted_cells_as_text(value):
    output = StringIO()
    generate_csv_report(value, {value: {'url_main': value, 'url_user': value}}, output)
    row = list(csv.reader(StringIO(output.getvalue())))[1]
    assert row[:4] == ["'" + value] * 4
