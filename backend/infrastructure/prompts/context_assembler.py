import jinja2
import tiktoken
from typing import List, Dict

class ContextAssembler:
    def __init__(self, templates_dir: str):
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def render_prompt(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text) // 4  # Fallback rough estimate

    def truncate_history(self, history: List[Dict[str, str]], max_tokens: int = 4000) -> List[Dict[str, str]]:
        current_tokens = 0
        truncated = []
        for msg in reversed(history):
            tokens = self.count_tokens(msg.get("content", ""))
            if current_tokens + tokens > max_tokens:
                break
            truncated.insert(0, msg)
            current_tokens += tokens
        return truncated
