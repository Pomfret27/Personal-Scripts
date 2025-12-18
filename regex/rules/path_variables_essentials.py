import re

RULE_NAME = "路径变量（基本）"
RULE_DESCRIPTION = "将 Windows 绝对路径转换为路径变量格式，只使用 <home> <winDocuments> <winProgramData>"

def get_pattern():
    return (
        r"(?P<winProgramData>C:\\ProgramData)" "|"
        r"(?P<winDocuments>C:\\Users\\[^\\]+\\(?:OneDrive\\)?(?:Documents|文档))" "|"
        r"(?P<home>C:\\Users\\[^\\]+)" "|"
        r"(?P<slash>\\)"
    )

def get_replacement(match):
    if match.group('slash'):
        return '/'
    elif match.group('winProgramData'):
        return '<winProgramData>'
    elif match.group('winDocuments'):
        return '<winDocuments>'
    elif match.group('home'):
        return '<home>'


if __name__ == '__main__':
    test_text = r"C:\Users\Pomfret\OneDrive\文档\AliceSoft\多娜多娜"
    pattern = re.compile(get_pattern())
    result = pattern.sub(get_replacement, test_text)

    print(f"规则测试: {RULE_NAME}")
    print(f"输入: {test_text}")
    print(f"输出: {result}")
    # print(f"预期: <winDocuments>/AliceSoft/多娜多娜")
    # print(f"测试: {'通过' if result == '<winDocuments>/AliceSoft/多娜多娜' else '失败'}")