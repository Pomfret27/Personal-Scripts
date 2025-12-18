import re

RULE_NAME = "路径变量（全部）"
RULE_DESCRIPTION = "将 Windows 绝对路径转换为路径变量格式，使用所有 Windows 路径变量"

def get_pattern():
    return (
        r"(?P<winPublic>C:\\Users\\Public)" "|"
        r"(?P<winProgramData>C:\\ProgramData)" "|"
        r"(?P<winDir>C:\\Windows)" "|"
        r"(?P<winAppData>C:\\Users\\[^\\]+\\AppData\\Roaming)" "|"
        r"(?P<winLocalAppDataLow>C:\\Users\\[^\\]+\\AppData\\LocalLow)" "|"
        r"(?P<winLocalAppData>C:\\Users\\[^\\]+\\AppData\\Local)" "|"
        r"(?P<winDocuments>C:\\Users\\[^\\]+\\(?:OneDrive\\)?(?:Documents|文档))" "|"
        r"(?P<home>C:\\Users\\[^\\]+)" "|"
        r"(?P<slash>\\)"
    )

def get_replacement(match):
    if match.group('slash'):
        return '/'
    elif match.group('winPublic'):
        return '<winPublic>'
    elif match.group('winProgramData'):
        return '<winProgramData>'
    elif match.group('winDir'):
        return '<winDir>'
    elif match.group('winAppData'):
        return '<winAppData>'
    elif match.group('winLocalAppDataLow'):
        return '<winLocalAppDataLow>'
    elif match.group('winLocalAppData'):
        return '<winLocalAppData>'
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