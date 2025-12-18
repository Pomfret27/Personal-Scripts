"""
engine.py - 正则规则引擎
职责：动态加载和管理 rules/ 目录下的所有规则插件，并提供统一的调用接口。
"""
import os
import importlib.util
import re
from typing import Dict, List, Optional, Callable

# 类型注解：定义规则函数的标准类型，提高代码可读性和IDE支持
PatternFunc = Callable[[], str]
ReplacementFunc = Callable[[re.Match], str]

class _RegexRule:
    """
    内部类：封装单个正则规则。
    对外隐藏实现细节，仅通过 `apply()` 方法提供执行接口。
    """
    def __init__(self, name: str, description: str, pattern_func: PatternFunc, repl_func: ReplacementFunc):
        """
        初始化一个规则对象。
        参数:
            name: 规则中文名 (来自 RULE_NAME)
            description: 规则描述 (来自 RULE_DESCRIPTION)
            pattern_func: 返回正则表达式字符串的函数 (get_pattern)
            repl_func: 执行替换的回调函数 (get_replacement)
        """
        self.name = name
        self.description = description
        self._pattern_func = pattern_func
        self._repl_func = repl_func
        # 惰性编译：第一次使用时才编译正则，优化启动速度
        self._compiled_pattern: Optional[re.Pattern] = None

    def _compile(self) -> re.Pattern:
        """编译正则表达式（如果尚未编译）。"""
        if self._compiled_pattern is None:
            pattern_str = self._pattern_func()
            # 使用 VERBOSE 模式允许正则字符串中的空格和注释，保持与规则文件一致
            self._compiled_pattern = re.compile(pattern_str, re.VERBOSE)
        return self._compiled_pattern

    def apply(self, text: str) -> str:
        """
        应用规则到文本，返回处理后的结果。
        这是本类对外暴露的核心方法。
        """
        try:
            pattern = self._compile()
            # 关键调用：使用 sub 方法，将匹配到的部分用自定义函数替换
            return pattern.sub(self._repl_func, text)
        except re.error as e:
            # 如果正则本身有误，返回错误信息（在GUI中可看到）
            return f"[正则错误] {self.name}: {str(e)}"
        except Exception as e:
            # 捕获替换函数中可能的其他异常
            return f"[执行错误] {self.name}: {str(e)}"

class RuleEngine:
    """
    规则引擎主类。
    采用单例模式的思想，全局通常只需要一个引擎实例。
    """
    def __init__(self, rules_dir: str = "rules"):
        """
        初始化引擎并加载指定目录下的所有规则。
        参数:
            rules_dir: 存放规则.py文件的目录路径
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.rules_dir = os.path.join(base_dir, rules_dir)
        # 核心存储：规则名 -> _RegexRule 对象
        self._rules: Dict[str, _RegexRule] = {}
        self._load_rules()

    def _load_rules(self) -> None:
        """加载 rules_dir 目录下所有合法的规则模块。"""
        # 1. 检查规则目录是否存在
        if not os.path.isdir(self.rules_dir):
            print(f"[引擎] 警告：规则目录 '{self.rules_dir}' 不存在。")
            return

        # 2. 列出目录下所有 .py 文件（排除 __init__.py）
        for filename in os.listdir(self.rules_dir):
            if not filename.endswith('.py') or filename == '__init__.py':
                continue  # 跳过非Python文件或初始化文件

            # 3. 从文件路径动态加载模块
            rule_name = filename[:-3]  # 去掉 '.py' 后缀作为临时名称
            module_path = os.path.join(self.rules_dir, filename)
            self._load_single_rule(rule_name, module_path)

        print(f"[引擎] 加载完成，共找到 {len(self._rules)} 个规则。")

    def _load_single_rule(self, module_name: str, filepath: str) -> None:
        """
        尝试加载单个规则文件。
        使用 importlib 实现动态导入，避免依赖预知的模块名。
        """
        try:
            # 1. 创建模块规格并加载
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                print(f"[引擎] 警告：无法为文件 '{filepath}' 创建规格。")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # 执行模块代码

            # 2. 验证模块是否包含必需的接口
            required_attrs = ['RULE_NAME', 'get_pattern', 'get_replacement']
            for attr in required_attrs:
                if not hasattr(module, attr):
                    print(f"[引擎] 警告：文件 '{filepath}' 缺少必需属性 '{attr}'，已跳过。")
                    return

            # 3. 获取规则元信息和函数
            rule_name = module.RULE_NAME
            # 使用 getattr 并设置默认值，增强容错性
            rule_description = getattr(module, 'RULE_DESCRIPTION', '暂无描述')
            pattern_func = module.get_pattern
            repl_func = module.get_replacement

            # 4. 创建规则对象并存入字典
            rule = _RegexRule(rule_name, rule_description, pattern_func, repl_func)
            self._rules[rule_name] = rule
            print(f"[引擎] 成功加载规则: {rule_name}")

        except SyntaxError as e:
            # 规则文件本身有语法错误
            print(f"[引擎] 语法错误：无法加载文件 '{filepath}'。错误: {e}")
        except Exception as e:
            # 捕获其他所有异常，防止一个规则加载失败导致引擎崩溃
            print(f"[引擎] 未知错误：加载文件 '{filepath}' 时失败。错误: {e}")

    def get_rule_names(self) -> List[str]:
        """
        获取所有已加载规则的名称列表。
        主要用于 GUI 下拉框的选项。
        """
        # 返回排序后的列表，确保下拉框选项顺序固定
        return sorted(self._rules.keys())

    def get_rule_description(self, rule_name: str) -> str:
        """
        获取指定规则的描述信息。
        用于 GUI 中显示规则说明。
        """
        rule = self._rules.get(rule_name)
        return rule.description if rule else "规则不存在"

    def apply_rule(self, rule_name: str, text: str) -> str:
        """
        应用指定规则处理文本。
        这是引擎对外提供的核心服务接口。
        """
        rule = self._rules.get(rule_name)
        if rule:
            return rule.apply(text)
        # 如果规则不存在，原样返回文本并提示（在GUI中可看到）
        return f"[规则未找到] 名称 '{rule_name}' 的规则不存在。\n{text}"

    def rule_exists(self, rule_name: str) -> bool:
        """检查指定名称的规则是否存在。"""
        return rule_name in self._rules

# 创建全局引擎实例，方便导入使用
# 在 main.py 中可以直接：from engine import global_engine
global_engine = RuleEngine()

# 以下代码仅当直接运行 engine.py 时执行，用于测试引擎本身
if __name__ == "__main__":
    print("=" * 50)
    print("规则引擎独立测试")
    print("=" * 50)

    # 1. 测试引擎初始化
    test_engine = RuleEngine("rules")  # 默认就是 "rules"
    print(f"规则列表: {test_engine.get_rule_names()}")

    # 2. 测试规则描述获取
    for name in test_engine.get_rule_names():
        desc = test_engine.get_rule_description(name)
        print(f"  - {name}: {desc[:30]}...")

    # 3. 测试规则应用（如果存在规则的话）
    if test_engine.get_rule_names():
        test_text = r"C:\Users\测试用户\Desktop\test.txt 和 C:\ProgramData\App\config.ini"
        first_rule = test_engine.get_rule_names()[0]
        result = test_engine.apply_rule(first_rule, test_text)
        print(f"\n测试规则: {first_rule}")
        print(f"输入文本: {test_text}")
        print(f"处理结果: {result}")