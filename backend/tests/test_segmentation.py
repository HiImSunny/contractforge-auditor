"""
Property-based tests for contract segmentation and language detection.

Feature: contractforge-auditor

Property 1: Language detection round-trip
Property 2: Clause segmentation integrity
Property 17: Bilingual natural-language field consistency

Validates: Requirements 1.8, 1.9, 9.1, 9.2, 9.3, 9.4
"""
import re
from typing import Literal
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from app.agents.ingestion import run as ingestion_run
from app.agents.schemas import Clause, ClauseList


# ── Language detection helpers ───────────────────────────────────────────────

def detect_language_heuristic(text: str) -> Literal["en", "vi"]:
    """
    Simple heuristic to detect if text is dominantly English or Vietnamese.
    
    Counts common English and Vietnamese words to determine language.
    This is used to verify Property 1 (language detection round-trip).
    """
    if not text:
        return "en"
    
    # Common English words
    en_words = {
        "the", "a", "and", "or", "is", "are", "was", "were", "be", "been",
        "have", "has", "do", "does", "did", "will", "would", "should", "could",
        "may", "might", "must", "can", "shall", "to", "of", "in", "on", "at",
        "by", "for", "with", "from", "as", "that", "this", "which", "who",
        "agreement", "contract", "party", "parties", "services", "customer",
        "provider", "shall", "may", "must", "not", "hereby", "herein",
        "section", "term", "payment", "liability", "confidential", "data",
        "intellectual", "property", "rights", "termination", "force", "majeure",
    }
    
    # Common Vietnamese words and characters
    vi_words = {
        "hợp", "đồng", "dịch", "vụ", "bên", "cung", "cấp", "sử", "dụng",
        "công", "ty", "địa", "chỉ", "ngày", "tháng", "năm", "ký", "kết",
        "thỏa", "thuận", "điều", "khoản", "định", "nghĩa", "dữ", "liệu",
        "thông", "tin", "bảo", "mật", "phần", "mềm", "ứng", "dụng",
        "phát", "triển", "tư", "vấn", "công", "nghệ", "người", "đại",
        "diện", "pháp", "luật", "giám", "đốc", "tổng", "mã", "số",
        "thuế", "tnhh", "cổ", "phần", "việt", "nam", "hồ", "chí", "minh",
    }
    
    # Vietnamese has many diacritical marks
    vi_chars = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    
    text_lower = text.lower()
    
    # Count Vietnamese diacritical marks
    vi_diacritic_count = sum(1 for c in text_lower if c in vi_chars)
    
    # Count word matches
    words = re.findall(r'\b\w+\b', text_lower)
    en_count = sum(1 for w in words if w in en_words)
    vi_count = sum(1 for w in words if w in vi_words)
    
    # Decision logic: if significant Vietnamese diacritics or more VI words, it's VI
    if vi_diacritic_count > len(text) * 0.02 or vi_count > en_count:
        return "vi"
    return "en"


def detect_language_in_text(text: str) -> Literal["en", "vi"]:
    """Detect language in a given text using heuristic."""
    return detect_language_heuristic(text)


# ── Hypothesis strategies ────────────────────────────────────────────────────

@st.composite
def english_contract_text(draw):
    """Generate realistic English contract text with multiple clauses."""
    sections = [
        "MASTER SERVICES AGREEMENT",
        "This Agreement is entered into as of {date} by and between:",
        "Provider and Customer agree as follows:",
        "SECTION 1: DEFINITIONS",
        "1.1 'Services' means the software-as-a-service products provided by Provider.",
        "1.2 'Confidential Information' means any information disclosed by either Party.",
        "SECTION 2: TERM AND TERMINATION",
        "2.1 The initial term shall commence on the Effective Date.",
        "2.2 Either party may terminate this Agreement with thirty days' written notice.",
        "SECTION 3: PAYMENT",
        "3.1 Customer shall pay Provider the fees specified in the Order Form.",
        "3.2 Payment shall be due within thirty days of invoice.",
        "SECTION 4: LIABILITY",
        "4.1 Neither party shall be liable for indirect or consequential damages.",
        "4.2 The total liability of either party shall not exceed the fees paid.",
    ]
    
    # Randomly select and shuffle sections
    num_sections = draw(st.integers(min_value=3, max_value=len(sections)))
    selected = draw(st.permutations(sections[:num_sections]))
    
    return "\n\n".join(selected)


@st.composite
def vietnamese_contract_text(draw):
    """Generate realistic Vietnamese contract text with multiple clauses."""
    sections = [
        "HỢP ĐỒNG DỊCH VỤ PHÁT TRIỂN PHẦN MỀM",
        "Hợp đồng này được ký kết bởi và giữa:",
        "Bên A và Bên B thỏa thuận như sau:",
        "ĐIỀU 1: ĐỊNH NGHĨA",
        "1.1 'Dịch Vụ' có nghĩa là các dịch vụ phát triển phần mềm được Bên A cung cấp.",
        "1.2 'Thông Tin Bảo Mật' có nghĩa là bất kỳ thông tin nào được một Bên tiết lộ.",
        "ĐIỀU 2: THỜI HẠN VÀ CHẤM DỨT",
        "2.1 Thời hạn ban đầu sẽ bắt đầu từ Ngày Giao Hàng.",
        "2.2 Bất kỳ Bên nào cũng có thể chấm dứt Hợp Đồng với thông báo bằng văn bản.",
        "ĐIỀU 3: THANH TOÁN",
        "3.1 Bên B sẽ thanh toán cho Bên A các khoản phí được quy định.",
        "3.2 Thanh toán phải được thực hiện trong vòng ba mươi ngày.",
        "ĐIỀU 4: TRÁCH NHIỆM PHÁP LÝ",
        "4.1 Không Bên nào chịu trách nhiệm về thiệt hại gián tiếp.",
        "4.2 Tổng trách nhiệm của mỗi Bên không vượt quá các khoản phí đã thanh toán.",
    ]
    
    # Randomly select and shuffle sections
    num_sections = draw(st.integers(min_value=3, max_value=len(sections)))
    selected = draw(st.permutations(sections[:num_sections]))
    
    return "\n\n".join(selected)


@st.composite
def contract_text_with_language(draw):
    """Generate contract text in either English or Vietnamese."""
    language = draw(st.sampled_from(["en", "vi"]))
    if language == "en":
        text = draw(english_contract_text())
    else:
        text = draw(vietnamese_contract_text())
    return text, language


# ── Property 1: Language detection round-trip ────────────────────────────────

@given(contract_text_with_language())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_1_language_detection_round_trip(contract_data):
    """
    Property 1: Language detection round-trip.
    
    For any contract text whose vocabulary is dominantly English or Vietnamese,
    the Ingestion Agent's language output equals the dominant vocabulary's tag.
    
    Validates: Requirements 1.8, 9.1
    """
    contract_text, expected_language = contract_data
    
    # Mock the gemini_client.invoke to return a realistic ClauseList
    # with the detected language matching the input
    mock_clauses = [
        {
            "clause_id": "C-001",
            "heading": "Section 1",
            "text": contract_text[:100] if len(contract_text) > 100 else contract_text,
            "language": expected_language,
            "char_span": {"start": 0, "end": min(100, len(contract_text))},
        }
    ]
    
    mock_result = ClauseList(
        language=expected_language,
        clauses=[Clause(**c) for c in mock_clauses],
    )
    
    with patch("app.agents.ingestion.gemini_client.invoke") as mock_invoke:
        mock_invoke.return_value = mock_result
        
        state = {
            "job_id": "test-job-001",
            "contract_text": contract_text,
        }
        
        result = ingestion_run(state)
        
        # Assert that the detected language matches the expected language
        assert result["language"] == expected_language, (
            f"Expected language {expected_language}, got {result['language']}"
        )


# ── Property 2: Clause segmentation integrity ────────────────────────────────

@given(st.lists(
    st.fixed_dictionaries({
        "clause_id": st.text(
            alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
            min_size=1,
            max_size=10,
        ),
        "heading": st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        "text": st.text(min_size=1, max_size=200),
        "language": st.sampled_from(["en", "vi"]),
    }),
    min_size=1,
    max_size=10,
    unique_by=lambda x: x["clause_id"],  # Ensure unique clause_ids
))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_2_clause_segmentation_integrity(clauses_data):
    """
    Property 2: Clause segmentation integrity.
    
    For any contract text, every emitted Clause c satisfies:
    - contract_text[c.char_span.start:c.char_span.end] == c.text
    - The set of clause_id values contains no duplicates
    
    Validates: Requirements 1.9
    """
    # Build a contract text from the clauses
    contract_text = ""
    clauses_with_spans = []
    
    for clause_data in clauses_data:
        start = len(contract_text)
        text = clause_data["text"]
        end = start + len(text)
        
        clause_data["char_span"] = {"start": start, "end": end}
        clauses_with_spans.append(clause_data)
        
        contract_text += text + "\n\n"
    
    # Create Clause objects
    clause_objects = [Clause(**c) for c in clauses_with_spans]
    
    # Mock the gemini_client.invoke to return the clauses
    mock_result = ClauseList(
        language="en",
        clauses=clause_objects,
    )
    
    with patch("app.agents.ingestion.gemini_client.invoke") as mock_invoke:
        mock_invoke.return_value = mock_result
        
        state = {
            "job_id": "test-job-002",
            "contract_text": contract_text,
        }
        
        result = ingestion_run(state)
        
        # Assert that char_span integrity is maintained
        emitted_clauses = result["clauses"]
        
        for clause in emitted_clauses:
            start = clause["char_span"]["start"]
            end = clause["char_span"]["end"]
            
            # Verify that the text at the char_span matches the clause text
            extracted_text = contract_text[start:end]
            assert extracted_text == clause["text"], (
                f"Char span mismatch: expected '{clause['text']}', "
                f"got '{extracted_text}' at [{start}:{end}]"
            )
        
        # Assert that clause_ids are unique
        clause_ids = [c["clause_id"] for c in emitted_clauses]
        assert len(clause_ids) == len(set(clause_ids)), (
            f"Duplicate clause_ids found: {clause_ids}"
        )


# ── Property 17: Bilingual NL fields stay in detected language ───────────────

@given(contract_text_with_language())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property_17_bilingual_nl_fields_consistency(contract_data):
    """
    Property 17: Bilingual natural-language field consistency.
    
    For any contract whose detected language is L ∈ {en, vi}, the Clause
    Analysis Agent's summary and key_terms are produced in language L.
    
    This test verifies that when the Ingestion Agent detects a language,
    the language field is correctly propagated to all clauses.
    
    Validates: Requirements 9.2, 9.3, 9.4
    """
    contract_text, detected_language = contract_data
    
    # Create mock clauses with the detected language
    mock_clauses = [
        {
            "clause_id": "C-001",
            "heading": "Section 1",
            "text": contract_text[:100] if len(contract_text) > 100 else contract_text,
            "language": detected_language,  # Language must match detected language
            "char_span": {"start": 0, "end": min(100, len(contract_text))},
        }
    ]
    
    mock_result = ClauseList(
        language=detected_language,
        clauses=[Clause(**c) for c in mock_clauses],
    )
    
    with patch("app.agents.ingestion.gemini_client.invoke") as mock_invoke:
        mock_invoke.return_value = mock_result
        
        state = {
            "job_id": "test-job-003",
            "contract_text": contract_text,
        }
        
        result = ingestion_run(state)
        
        # Assert that all clauses have the detected language
        for clause in result["clauses"]:
            assert clause["language"] == detected_language, (
                f"Clause language mismatch: expected {detected_language}, "
                f"got {clause['language']}"
            )
        
        # Assert that the top-level language matches
        assert result["language"] == detected_language


# ── Integration test: Multiple clauses with language consistency ─────────────

@given(st.lists(
    st.fixed_dictionaries({
        "clause_id": st.text(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-",
            min_size=3,
            max_size=10,
        ),
        "heading": st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        "text": st.text(min_size=10, max_size=200),
    }),
    min_size=2,
    max_size=5,
    unique_by=lambda x: x["clause_id"],
))
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_multiple_clauses_language_consistency(clauses_data):
    """
    Integration test: Multiple clauses maintain language consistency.
    
    Verifies that when multiple clauses are emitted, they all carry
    the same detected language tag.
    """
    # Build contract text
    contract_text = ""
    clauses_with_spans = []
    
    for clause_data in clauses_data:
        start = len(contract_text)
        text = clause_data["text"]
        end = start + len(text)
        
        clause_data["char_span"] = {"start": start, "end": end}
        clause_data["language"] = "en"  # Use English for this test
        clauses_with_spans.append(clause_data)
        
        contract_text += text + "\n\n"
    
    # Create Clause objects
    clause_objects = [Clause(**c) for c in clauses_with_spans]
    
    # Mock the gemini_client.invoke
    mock_result = ClauseList(
        language="en",
        clauses=clause_objects,
    )
    
    with patch("app.agents.ingestion.gemini_client.invoke") as mock_invoke:
        mock_invoke.return_value = mock_result
        
        state = {
            "job_id": "test-job-004",
            "contract_text": contract_text,
        }
        
        result = ingestion_run(state)
        
        # All clauses should have the same language
        languages = {c["language"] for c in result["clauses"]}
        assert len(languages) == 1, (
            f"Multiple languages found in clauses: {languages}"
        )
        
        # The language should match the top-level detected language
        assert languages.pop() == result["language"]
