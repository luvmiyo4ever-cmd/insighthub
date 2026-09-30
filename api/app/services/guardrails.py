"""Small deterministic guardrails for the InsightHub chat boundary.

The RAG model receives untrusted document text. These checks are deliberately
provider-independent so a local or commercial model cannot bypass the basic
privacy and action boundary through prompt wording or retrieved content.
"""

from dataclasses import dataclass
import re


_PROMPT_PATTERNS = (
    r"\bsystem\s+prompt\b",
    r"\bdeveloper\s+(?:message|instruction)\b",
    r"\bhidden\s+(?:prompt|instruction)s?\b",
    r"\b(?:reveal|print|show|disclose|extract)\b.{0,80}\bprompt\b",
    r"(?:prompt|chỉ dẫn|hướng dẫn)\s+(?:hệ thống|ẩn)",
    r"(?:lộ|tiết lộ|in ra|trích xuất).{0,80}(?:prompt|chỉ dẫn hệ thống)",
)

_PII_PATTERNS = (
    r"\bpii\b",
    r"(?:personal|private|sensitive)\s+(?:information|data|details)",
    r"(?:thông tin|dữ liệu)\s+cá nhân",
    r"(?:số điện thoại|địa chỉ nhà|email cá nhân|số căn cước|cccd|hộ chiếu)",
    r"(?:tài khoản ngân hàng|hồ sơ bệnh án|mật khẩu|api\s*key|secret)",
)

_ACTION_REQUEST_PATTERNS = (
    r"(?:please|can you|could you|would you).{0,100}(?:send|delete|remove|"
    r"upload|download|re-?index|share|publish|email|message|link|database|"
    r"drive|url)",
    r"(?:hãy|vui lòng|giúp tôi|thực hiện).{0,100}(?:gửi email|gửi thư|xóa|"
    r"xoá|tải lên|tải xuống|đăng công khai|chia sẻ|lưu đè|đổi quyền|"
    r"cập nhật cơ sở dữ liệu)",
    r"^(?:gửi email|gửi thư|xóa|xoá|tải lên|tải xuống|đăng công khai|chia sẻ)",
    r"^(?:send|delete|remove|upload|download|re-?index|share|publish)\b",
    r"(?:google\s+drive|message\s+id|public\s+(?:url|link))",
)

_CONTEXT_ACTION_PATTERNS = (
    r"(?:ignore|bỏ qua|follow|làm theo|must|should|phải|hãy).{0,120}(?:send|"
    r"email|delete|remove|upload|download|share|publish|gửi|xóa|xoá|tải lên|"
    r"chia sẻ|đăng công khai)",
)

_OUTPUT_ACTION_PATTERNS = (
    r"(?:i|we|the system)\s+(?:have|has|will)\s+(?:sent|deleted|uploaded|"
    r"shared|published|downloaded)",
    r"(?:đã|sẽ|vừa)\s+(?:gửi email|gửi thư|xóa|xoá|tải lên|tải xuống|chia sẻ|"
    r"đăng công khai)",
    r"(?:message\s+id|public\s+(?:url|link))\s*[:#]",
)

_DOCUMENT_INJECTION_PATTERNS = (
    r"ignore\s+(?:all\s+)?previous",
    r"bỏ qua\s+(?:mọi\s+)?(?:quy tắc|hướng dẫn|chỉ dẫn)",
    r"follow\s+(?:the|this)\s+(?:document|instruction)",
    r"làm theo\s+(?:chỉ dẫn|hướng dẫn)\s+(?:trong|của)\s+(?:tài liệu|pdf|tệp)",
    r"(?:retrieved|uploaded)\s+(?:document|content).{0,80}(?:must|should|tell you)",
    r"tài liệu.{0,80}(?:phải|hãy|yêu cầu bạn)",
)

_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)")


@dataclass(frozen=True)
class GuardrailDecision:
    blocked: bool
    category: str = ""


SAFE_REFUSAL = (
    "Tôi không thể thực hiện yêu cầu đó. Tài liệu truy xuất chỉ là dữ liệu "
    "không đáng tin cậy; tôi không tiết lộ chỉ dẫn ẩn hoặc dữ liệu cá nhân, "
    "và không thực hiện hành động bên ngoài phiên chat."
)


def _matches(patterns: tuple[str, ...], value: str) -> bool:
    return any(re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def inspect_request(question: str) -> GuardrailDecision:
    """Block direct requests outside the read-only RAG chat contract."""

    if _matches(_PROMPT_PATTERNS, question):
        return GuardrailDecision(True, "prompt-extraction")
    if _matches(_PII_PATTERNS, question):
        return GuardrailDecision(True, "pii")
    if _matches(_ACTION_REQUEST_PATTERNS, question):
        return GuardrailDecision(True, "excessive-agency")
    return GuardrailDecision(False)


def inspect_context(contexts: list[dict]) -> GuardrailDecision:
    """Treat retrieved text as data and reject embedded executable instructions."""

    text = "\n".join(str(item.get("chunk_text", "")) for item in contexts)
    if _matches(_DOCUMENT_INJECTION_PATTERNS, text):
        return GuardrailDecision(True, "indirect-prompt-injection")
    if _matches(_PROMPT_PATTERNS, text):
        return GuardrailDecision(True, "prompt-extraction")
    if _matches(_PII_PATTERNS, text):
        return GuardrailDecision(True, "pii")
    if _matches(_CONTEXT_ACTION_PATTERNS, text):
        return GuardrailDecision(True, "excessive-agency")
    return GuardrailDecision(False)


def inspect_output(answer: str) -> GuardrailDecision:
    """Apply a final response boundary before returning data to the caller."""

    if _matches(_PROMPT_PATTERNS, answer):
        return GuardrailDecision(True, "prompt-extraction")
    if _matches(_OUTPUT_ACTION_PATTERNS, answer):
        return GuardrailDecision(True, "excessive-agency")
    if _EMAIL_PATTERN.search(answer) or _PHONE_PATTERN.search(answer):
        return GuardrailDecision(True, "pii")
    return GuardrailDecision(False)


def check(question: str, contexts: list[dict]) -> GuardrailDecision:
    """Run request and retrieved-context checks before a model call."""

    decision = inspect_request(question)
    if decision.blocked:
        return decision
    return inspect_context(contexts)
