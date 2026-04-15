from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    REFACTORING = 'refactoring'
    VALIDATOR = 'validator'
    TESTING = 'testing'
    BOOK_FINDER = 'book_finder'
    BOOK_ENCODER = 'book_encoder'


class ValidationStatus(str, Enum):
    VERIFIED_STATIC = 'verified_static'
    VERIFIED_TESTED = 'verified_tested'
    ASSUMED = 'assumed'
    FAILED = 'failed'
    MISSING = 'missing'
    MANUAL_REVIEW = 'manual_review'


class RiskLevel(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class EvidenceStrength(str, Enum):
    CODE_TRACE = 'code_trace'
    SEMANTIC_MATCH = 'semantic_match'
    TEST_EVIDENCE = 'test_evidence'
    INFERENCE = 'inference'
    NONE = 'none'


class RefactorMode(str, Enum):
    AUTO = 'auto'
    REVIEW = 'review'
    BLOCKED = 'blocked'


class PromptVersionRef(BaseModel):
    agent: str
    version: str
    sha256: str | None = None


class CodeArtifact(BaseModel):
    language: str
    content: str
    path: str | None = None
    framework: str | None = None


class Requirement(BaseModel):
    requirement_id: str
    text: str
    domain: str | None = None
    priority: Literal['must', 'should', 'could'] = 'must'


class BooksRef(BaseModel):
    category: str
    book_slug: str
    topic_file: str
    version: str | None = None


class ValidationScore(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    risk: RiskLevel
    evidence_strength: EvidenceStrength
    semantic_similarity: float | None = Field(default=None, ge=0.0, le=1.0)
    static_signal: float | None = Field(default=None, ge=0.0, le=1.0)
    test_signal: float | None = Field(default=None, ge=0.0, le=1.0)


class TestRequest(BaseModel):
    requirement_id: str
    assumption: str
    verification_goal: str
    code_reference: str
    suggested_inputs: list[str] = []
    expected_behavior: str
    failure_signature: str


class TestResult(BaseModel):
    requirement_id: str
    passed: bool | None = None
    evidence: str
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)


class RequirementValidation(BaseModel):
    requirement_id: str
    status: ValidationStatus
    evidence: str
    score: ValidationScore
    test_request: TestRequest | None = None


class DiffImpact(BaseModel):
    lines_added: int = 0
    lines_removed: int = 0
    files_touched: int = 1
    public_api_changed: bool = False
    estimated_blast_radius: RiskLevel = RiskLevel.LOW


class RefactoringChange(BaseModel):
    description: str
    pattern: str | None = None
    risk: RiskLevel = RiskLevel.LOW
    reversible: bool = True
    diff_impact: DiffImpact = Field(default_factory=DiffImpact)


class RefactoringInput(BaseModel):
    task_id: str
    code: CodeArtifact
    constraints: list[str] = []
    books_refs: list[BooksRef] = []
    approval_required: bool = False


class RefactoringOutput(BaseModel):
    task_id: str
    original_code: CodeArtifact
    refactored_code: CodeArtifact
    changes: list[RefactoringChange]
    behavior_guarantee: str
    aggregate_risk: RiskLevel
    aggregate_confidence: float = Field(ge=0.0, le=1.0)
    refactor_mode: RefactorMode


class ValidationInput(BaseModel):
    task_id: str
    code: CodeArtifact
    requirements: list[Requirement]
    books_refs: list[BooksRef] = []
    phase: Literal['static', 'final'] = 'static'
    test_results: list[TestResult] = []


class ValidationOutput(BaseModel):
    task_id: str
    phase: Literal['static', 'final']
    validations: list[RequirementValidation]
    overall_confidence: float = Field(ge=0.0, le=1.0)
    overall_risk: RiskLevel


class CoverageEntry(BaseModel):
    requirement_id: str
    covered: bool
    test_names: list[str] = []
    note: str | None = None


class TestCoverageInput(BaseModel):
    task_id: str
    mode: Literal['validation', 'coverage']
    code: CodeArtifact
    requirements: list[Requirement] = []
    test_requests: list[TestRequest] = []
    books_refs: list[BooksRef] = []


class TestCoverageOutput(BaseModel):
    task_id: str
    mode: Literal['validation', 'coverage']
    test_results: list[TestResult] = []
    coverage_matrix: list[CoverageEntry] = []
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    suite_code: str | None = None


class KnowledgeScore(BaseModel):
    tier: str
    quality_score: float = Field(ge=0.0, le=1.0)
    recency_score: float = Field(ge=0.0, le=1.0)
    usage_score: float = Field(ge=0.0, le=1.0)
    duplicate_of: str | None = None
    stale: bool = False


class BookRecord(BaseModel):
    slug: str
    title: str
    authors: list[str]
    category: str
    free_url: str | None = None
    topics_to_encode: list[str]
    knowledge_score: KnowledgeScore | None = None


class BookEncodingOutput(BaseModel):
    slug: str
    category: str
    created_files: list[str]
    version: str
    dedupe_action: Literal['new', 'merged', 'replaced', 'skipped']
