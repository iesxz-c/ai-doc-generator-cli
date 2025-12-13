from parser.python_parser import PythonParser
from parser.js_parser import JavaScriptParser


def test_python_parser():
	parser = PythonParser()
	result = parser.parse_file("sample_repo/sample.py")
	assert result["language"] == "python"
	assert "functions" in result
	print(result["ast"][:200])


def test_js_parser():
	parser = JavaScriptParser()
	result = parser.parse_file("sample_repo/sample.js")
	assert result["language"] == "javascript"
	assert "functions" in result
	print(result["ast"][:200])


if __name__ == "__main__":
	test_python_parser()
	test_js_parser()
	print("SUCCESS: Parsers working!")
