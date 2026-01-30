"""
Type definitions for BeagleMind QA System messages and responses.
"""

from typing import Dict, List, Any, Optional, Union
from typing_extensions import TypedDict


class ToolFunction(TypedDict):
    """Represents a tool function call specification"""
    name: str
    arguments: str  # JSON string of arguments


class ToolCall(TypedDict, total=False):
    """Represents a tool call from the LLM"""
    id: str
    function: ToolFunction


class Message(TypedDict, total=False):
    """Represents a conversation message"""
    role: str  # "user", "assistant", "tool", "system"
    content: str
    tool_calls: List[ToolCall]
    tool_call_id: str


class FileInfo(TypedDict, total=False):
    """File information for context documents"""
    name: str
    path: str
    type: str
    language: str


class ContextDocument(TypedDict, total=False):
    """A document used for context"""
    text: str
    metadata: Dict[str, Any]
    file_info: FileInfo


class ToolResult(TypedDict, total=False):
    """Result of executing a tool"""
    tool: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    requires_permission: bool
    user_approved: Optional[bool]


class SearchResult(TypedDict, total=False):
    """Result from document search"""
    documents: List[List[str]]
    metadatas: List[List[Dict[str, Any]]]
    distances: List[List[float]]
    ids: List[List[str]]


class SourceInfo(TypedDict, total=False):
    """Source information for responses"""
    text: str
    metadata: Dict[str, Any]
    file_info: FileInfo


class SearchInfo(TypedDict, total=False):
    """Search metadata for responses"""
    total_found: int
    backend_used: str
    model_used: str


class ConversationEntry(TypedDict, total=False):
    """A single conversation turn"""
    role: str
    content: str
    tool_calls: List[Dict[str, Any]]


class QAResponse(TypedDict, total=False):
    """Response from QA system methods"""
    success: bool
    answer: str
    conversation: List[ConversationEntry]
    tool_results: List[ToolResult]
    sources: List[SourceInfo]
    iterations_used: int
    search_info: SearchInfo
    error: str


class ChatWithToolsRequest(TypedDict, total=False):
    """Request parameters for chat_with_tools method"""
    question: str
    llm_backend: str
    model_name: str
    max_iterations: int
    temperature: float
    auto_approve: bool
    use_tools: bool


class AskQuestionRequest(TypedDict, total=False):
    """Request parameters for ask_question method"""
    question: str
    search_strategy: str
    llm_backend: str
    model_name: str
    max_iterations: int
    temperature: float
    auto_approve: bool
    use_tools: bool


class PermissionRequest(TypedDict):
    """Permission request for tool execution"""
    tool_name: str
    arguments: Dict[str, Any]
    description: str
    risks: List[str]


class MachineInfo(TypedDict, total=False):
    """Machine information for context"""
    platform: str
    architecture: str
    python_version: str
    cwd: str
    username: str


class ToolDefinition(TypedDict, total=False):
    """OpenAI-style tool definition"""
    type: str
    function: Dict[str, Any]


class LLMResponse(TypedDict, total=False):
    """Response from LLM API"""
    content: str
    tool_calls: List[ToolCall]
    finish_reason: str
    usage: Dict[str, Any]


# Union types for flexibility
MessageContent = Union[str, List[Dict[str, Any]]]
ToolArguments = Union[str, Dict[str, Any]]