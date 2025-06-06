def parse_rules(rule_text):
    """
    解析規則，每行格式："A" -> "B"
    """
    rules = []
    for line in rule_text.strip().splitlines():
        if '->' in line:
            src, dst = line.split('->', 1)
            # 移除雙引號及前後空白
            src = src.strip().strip('"')
            dst = dst.strip().strip('"')
            rules.append((src, dst))
    return rules


def batch_replace(rules, text):
    """
    依規則批次取代文字。
    """
    for src, dst in rules:
        text = text.replace(src, dst)
    return text
