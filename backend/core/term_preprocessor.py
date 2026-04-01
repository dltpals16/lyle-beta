"""
[Step 1] 용어 전처리
난임 커뮤니티 은어/줄임말을 의학 용어로 변환합니다.
"""
import json
import re
from config import TERM_DICT_PATH


class TermPreprocessor:
    def __init__(self, dict_path: str = TERM_DICT_PATH):
        self.exact_mappings: dict[str, str] = {}
        self.pattern_mappings: list[tuple[re.Pattern, str]] = []
        self._load(dict_path)

    def _load(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # exact 매핑 로드
            if "exact" in data:
                for item in data["exact"]:
                    if isinstance(item, dict):
                        slang = item.get("slang", item.get("term", ""))
                        medical = item.get("medical", item.get("mapped", ""))
                    else:
                        continue
                    if slang and medical:
                        self.exact_mappings[slang] = medical

            # pattern 매핑 로드
            if "patterns" in data:
                for item in data["patterns"]:
                    if isinstance(item, dict):
                        pattern = item.get("pattern", "")
                        replacement = item.get("replacement", item.get("mapped", ""))
                    else:
                        continue
                    if pattern and replacement:
                        try:
                            compiled = re.compile(pattern)
                            self.pattern_mappings.append((compiled, replacement))
                        except re.error:
                            continue

            print(f"[TermPreprocessor] exact: {len(self.exact_mappings)}개, "
                  f"patterns: {len(self.pattern_mappings)}개 로드 완료")

        except FileNotFoundError:
            print(f"[TermPreprocessor] 경고: {path} 파일을 찾을 수 없습니다. 빈 사전으로 진행.")
        except json.JSONDecodeError:
            print(f"[TermPreprocessor] 경고: {path} JSON 파싱 실패. 빈 사전으로 진행.")

    def process(self, text: str) -> str:
        """
        은어/줄임말을 의학 용어로 변환합니다.
        원본 표현도 괄호 안에 유지하여 벡터 검색 시 양쪽 모두 매칭 가능하게 합니다.
        """
        result = text

        # exact 매핑 적용
        for slang, medical in self.exact_mappings.items():
            if slang in result:
                # "배유제" → "배란유도제(배유제)" 형태로 변환
                result = result.replace(slang, f"{medical}({slang})")

        # pattern 매핑 적용
        for pattern, replacement in self.pattern_mappings:
            match = pattern.search(result)
            if match:
                original = match.group(0)
                replaced = pattern.sub(replacement, result)
                # 패턴 매칭은 단순 대체 (원본이 이미 replacement에 포함되는 경우가 많음)
                result = replaced

        return result

    def get_medical_terms(self, text: str) -> list[str]:
        """입력 텍스트에서 매칭되는 의학 용어 목록 반환"""
        terms = []
        for slang, medical in self.exact_mappings.items():
            if slang in text:
                terms.append(medical)
        return terms
