from scorekit.checker import validate_file
import pytest

def test_正常数据(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"method": "A", "logical": 80, "structural": 90}\n',
            encoding="utf-8")
    s = validate_file(p)
    assert s.total_lines == 1
    assert s.valid_count == 1
    assert s.avg_logical == 80.0


def test_混合数据(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"method": "A", "logical": 80, "structural": 90}\n'
            '{"method": "B", "logical": -3, "structural": 90}\n',
            encoding="utf-8")
    s = validate_file(p)
    assert s.total_lines == 2
    assert s.valid_count == 1
    assert s.avg_logical == 80.0

def test_末尾空行(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"method": "A", "logical": 80, "structural": 90}\n''\n',
            encoding="utf-8")
    s = validate_file(p)
    assert s.total_lines == 1
    assert s.valid_count == 1
    assert s.avg_logical == 80.0

def test_坏json(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{这不是一个json}\n',
            encoding="utf-8")
    s = validate_file(p)
    assert s.total_lines == 1
    assert s.valid_count == 0
    assert s.avg_logical == 0.0

def test_全坏(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"method": "A", "logical": 200, "structural": 90}\n'
            '{"method": "B", "logical": -3, "structural": 90}\n',
            encoding="utf-8")
    s = validate_file(p)
    assert s.total_lines == 2
    assert s.valid_count == 0
    assert s.avg_logical == 0.0

def test_文件不存在(tmp_path):
    p = tmp_path / "s.jsonl"
    
    with pytest.raises(FileNotFoundError):validate_file(p)