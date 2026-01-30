import json
import logging
import os
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
from .config import GROQ_API_KEY, RAG_BACKEND_URL, COLLECTION_NAME
from .tools_registry import enhanced_tool_registry_optimized as tool_registry

# Import modular services
from .services.llm_service import llm_service
from .services.search_service import SearchService
from .services.tool_service import tool_service
from .prompts.prompt_templates import PromptTemplates
from .prompts.prompt_generator import prompt_generator
from .helpers.conversation_manager import conversation_manager
from .helpers.permission_handler import permission_handler
from .helpers.utils import utils


# Setup logging - suppress verbose output
logging.basicConfig(level=logging.CRITICAL)  # Only show critical errors
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)



class QASystem:
    def __init__(self, backend_url: str = None, collection_name: str = None):
        # Get backend URL from config/environment with fallback to localhost
        if backend_url is None:
            # Try to get from environment variables first
            backend_url = RAG_BACKEND_URL

        self.backend_url = backend_url
        # Enforce beagleboard collection by default; allow explicit override if provided
        self.collection_name = collection_name or COLLECTION_NAME or 'beagleboard'

        # Initialize services
        self.search_service = SearchService(self.backend_url, self.collection_name)

        # Use global conversation manager
        self.conversation_manager = conversation_manager

        # Cap how many prior turns to include when sending prompts
        try:
            self.history_max_messages = int(os.getenv('MAX_HISTORY_MESSAGES', '20'))
        except Exception:
            self.history_max_messages = 20

    # ==== Conversation memory utilities ====
    def start_conversation(self):
        """Begin a new chat session (clears in-RAM history)."""
        self.conversation_manager.start_conversation()

    def reset_conversation(self):
        """Alias to start a new session by clearing history."""
        self.conversation_manager.reset_conversation()

    def _get_history_messages(self) -> List[Dict[str, str]]:
        """Return prior conversation turns as chat messages (capped)."""
        return self.conversation_manager.get_history_messages()

    def _record_user(self, content: str):
        self.conversation_manager.record_user(content)

    def _record_assistant(self, content: str):
        self.conversation_manager.record_assistant(content)

    def search(self, query: str, n_results: int = 5, rerank: bool = True, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Search documents using the backend API"""
        return self.search_service.search(query, n_results, rerank, collection_name)
    
    def _parse_tool_arguments(self, args_str: str, function_name: str) -> Dict[str, Any]:
        """Parse tool arguments from potentially malformed JSON"""
        try:
            return json.loads(args_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse arguments for {function_name}, attempting recovery")
            
            if function_name == "run_command":
                return self._parse_command_arguments(args_str)
            elif function_name == "write_file":
                return self._parse_write_file_arguments(args_str)
            else:
                return self._parse_generic_arguments(args_str)
    
    def _parse_command_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse command arguments from malformed JSON"""
        try:
            patterns = [
                r'"command":\s*"([^"]*)"',  # Standard pattern
                r'"command":\s*"([^"]*?)(?:"|$)',  # Pattern allowing unclosed quotes
                r'"command":\s*([^,}]*)',  # Pattern without quotes
            ]
            
            for pattern in patterns:
                command_match = re.search(pattern, args_str, re.DOTALL)
                if command_match:
                    command = command_match.group(1).strip()
                    command = ' '.join(command.split())
                    return {"command": command}
            
            # Extract anything that looks like a command
            lines = args_str.split('\n')
            for line in lines:
                if 'command' in line.lower():
                    cleaned = re.sub(r'[^a-zA-Z0-9\s\-\.\/_><=;]', ' ', line)
                    if cleaned.strip():
                        return {"command": "echo 'Extracted: " + cleaned.strip()[:50] + "'"}
            
            return {"command": "echo 'Could not parse command'"}
            
        except Exception:
            return {"command": "echo 'Command parsing failed'"}
    
    def _parse_write_file_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse write_file arguments from malformed JSON"""
        try:
            file_path_match = re.search(r'"file_path":\s*"([^"]*)"', args_str)
            content_match = re.search(r'"content":\s*"([^"]*)"', args_str, re.DOTALL)
            
            file_path = file_path_match.group(1) if file_path_match else "recovered_file.txt"
            content = content_match.group(1) if content_match else "# Content could not be recovered"
            
            return {
                "file_path": file_path,
                "content": content
            }
        except Exception:
            return {
                "file_path": "error_recovery.txt",
                "content": "# Failed to parse original content"
            }
    
    def _parse_generic_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse generic arguments from malformed JSON"""
        try:
            cleaned_args = re.sub(r'[\n\r\t]', ' ', args_str)
            cleaned_args = re.sub(r'\s+', ' ', cleaned_args)
            return json.loads(cleaned_args)
        except:
            return {}

    def _build_context_docs_from_search(self, search_results: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """Build context documents from search results"""
        context_docs = []
        
        if search_results and search_results.get('documents') and search_results['documents'] and search_results['documents'][0]:
            documents = search_results['documents'][0]
            metadatas = search_results.get('metadatas', [[]])[0]
            
            for i, doc_text in enumerate(documents[:max_results]):
                metadata = metadatas[i] if i < len(metadatas) else {}
                context_docs.append({
                    'text': doc_text,
                    'metadata': metadata,
                    'file_info': {
                        'name': metadata.get('file_name', 'Unknown'),
                        'path': metadata.get('file_path', ''),
                        'type': metadata.get('file_type', 'unknown'),
                        'language': metadata.get('language', 'unknown')
                    }
                })
        
        return context_docs

    def _execute_tool_call(self, tool_call: Dict[str, Any], messages: List[Dict[str, Any]], 
                          context_docs: List[Dict[str, Any]], auto_approve: bool) -> Dict[str, Any]:
        """Execute a single tool call and return the result"""
        function_name = tool_call["function"]["name"]
        
        try:
            function_args = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse function arguments: {e}")
            logger.error(f"Raw arguments: {tool_call['function']['arguments']}")
            function_args = {}
        
        # Handle virtual retrieval tool
        if function_name == "retrieve_context":
            q = function_args.get("query") or ""
            n_val = function_args.get("n_results", 5)
            try:
                n = int(n_val)
            except Exception:
                n = 5
            rr_val = function_args.get("rerank", True)
            if isinstance(rr_val, str):
                rr = rr_val.strip().lower() in ("1", "true", "yes", "y")
            else:
                rr = bool(rr_val)
            collection_override = function_args.get("collection_name") or function_args.get("collection")
            tool_result = self.search(q, n_results=n, rerank=rr, collection_name=collection_override)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", f"call_{len(messages)}"),
                "content": json.dumps(tool_result)
            })
            
            # Add to context docs
            if tool_result and tool_result.get('documents') and tool_result['documents'] and tool_result['documents'][0]:
                docs = tool_result['documents'][0]
                metas = tool_result.get('metadatas', [[]])[0]
                for i, doc_text in enumerate(docs[:5]):
                    md = metas[i] if i < len(metas) else {}
                    context_docs.append({
                        'text': doc_text,
                        'metadata': md,
                        'file_info': {
                            'name': md.get('file_name', 'Unknown'),
                            'path': md.get('file_path', ''),
                            'type': md.get('file_type', 'unknown'),
                            'language': md.get('language', 'unknown')
                        }
                    })
            
            return {
                "tool": function_name,
                "arguments": {"query": q, "n_results": n, "rerank": rr},
                "result": tool_result,
                "requires_permission": False,
                "user_approved": None
            }

        # Check if this requires permission
        requires_permission = function_name in ["write_file", "edit_file_lines"]
        user_approved = auto_approve
        
        # Import tool display for rich formatting
        from .cli.tool_display import tool_display
        
        if requires_permission and not auto_approve:
            permission_info = permission_handler.format_permission_request(function_name, function_args)
            tool_display.show_permission_request(function_name, permission_info)
            
            while True:
                user_input = input("\nDo you approve this operation? (y/n): ").strip().lower()
                if user_input in ['y', 'yes']:
                    user_approved = True
                    break
                elif user_input in ['n', 'no']:
                    user_approved = False
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        
        # Execute the tool if approved
        if user_approved or not requires_permission:
            tool_result = self.execute_tool(function_name, function_args)
            tool_display.show_tool_result(function_name, function_args, tool_result)
        else:
            tool_result = {
                "success": False,
                "error": "Operation cancelled by user",
                "user_denied": True
            }
            tool_display.show_operation_cancelled()
        
        # Add tool result to messages
        tool_content = json.dumps(tool_result) if tool_result else "{}"
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.get("id", f"call_{len(messages)}"),
            "content": tool_content
        })
        
        return {
            "tool": function_name,
            "arguments": function_args,
            "result": tool_result,
            "requires_permission": requires_permission,
            "user_approved": user_approved if requires_permission else None
        }

    def _build_context_string(self, context_docs: List[Dict[str, Any]]) -> str:
        """Build context string from context documents"""
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            try:
                file_info = doc.get('file_info', {})
                metadata = doc.get('metadata', {})
                doc_text = doc.get('text', '')
                
                context_part = f"Document {i}:\n"
                context_part += f"File: {file_info.get('name', 'Unknown')} ({file_info.get('type', 'unknown')})\n"
                
                if metadata.get('source_link'):
                    context_part += f"Source: {metadata.get('source_link')}\n"
                
                context_part += f"Content:\n{doc_text}\n"
                context_parts.append(context_part)
            except Exception as e:
                logger.warning(f"Error processing document {i}: {e}")
                continue
        
        return "\n" + "="*50 + "\n".join(context_parts) if context_parts else ""

    def _execute_tool_with_service(self, tool_call: Dict[str, Any], messages: List[Dict[str, Any]], 
                                  context_docs: List[Dict[str, Any]], auto_approve: bool, question: str) -> Dict[str, Any]:
        """Execute a tool call using the tool service"""
        function_name = tool_call["function"]["name"]
        
        # Handle virtual retrieval tool
        if function_name == "retrieve_context":
            function_args = tool_service.parse_tool_arguments(tool_call["function"]["arguments"], function_name)
            q = function_args.get("query") or question
            n_val = function_args.get("n_results", 5)
            try:
                n = int(n_val)
            except Exception:
                n = 5
            rr_val = function_args.get("rerank", True)
            if isinstance(rr_val, str):
                rr = rr_val.strip().lower() in ("1", "true", "yes", "y")
            else:
                rr = bool(rr_val)
            collection_override = function_args.get("collection_name") or function_args.get("collection")
            tool_result = self.search(q, n_results=n, rerank=rr, collection_name=collection_override)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", f"call_{len(messages)}"),
                "content": json.dumps(tool_result)
            })
            
            # Add to context docs
            if tool_result and tool_result.get('documents') and tool_result['documents'] and tool_result['documents'][0]:
                docs = tool_result['documents'][0]
                metas = tool_result.get('metadatas', [[]])[0]
                for i, doc_text in enumerate(docs[:5]):
                    md = metas[i] if i < len(metas) else {}
                    context_docs.append({
                        'text': doc_text,
                        'metadata': md,
                        'file_info': {
                            'name': md.get('file_name', 'Unknown'),
                            'path': md.get('file_path', ''),
                            'type': md.get('file_type', 'unknown'),
                            'language': md.get('language', 'unknown')
                        }
                    })
            
            return {
                "tool": function_name,
                "arguments": {"query": q, "n_results": n, "rerank": rr},
                "result": tool_result,
                "requires_permission": False,
                "user_approved": None
            }
        else:
            # Use the tool service for regular tool execution
            function_args = tool_service.parse_tool_arguments(tool_call["function"]["arguments"], function_name)
            execution_result = tool_service.execute_tool_with_feedback(function_name, function_args, auto_approve)
            
            # Add tool result to messages
            tool_content = json.dumps(execution_result["result"]) if execution_result["result"] else "{}"
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", f"call_{len(messages)}"),
                "content": tool_content
            })
            
            return {
                "tool": function_name,
                "arguments": function_args,
                "result": execution_result["result"],
                "requires_permission": execution_result["requires_permission"],
                "user_approved": execution_result["user_approved"]
            }

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return the OpenAI function definitions for all available tools"""
        return tool_service.get_available_tools()

    def _retrieve_tool_def(self) -> Dict[str, Any]:
        """Provide a virtual tool for retrieval that LLMs can call when needed (non-Ollama backends)."""
        return PromptTemplates.get_retrieve_context_tool()

    def _should_retrieve(self, question: str, backend: str, use_tools: bool) -> bool:
        """Heuristic for deciding retrieval when not using tool-driven chat."""
        return prompt_generator.should_retrieve(question, backend, use_tools)
    
    def execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function by name with given arguments"""
        return tool_service.execute_tool(function_name, function_args)
    
    def chat_with_tools(self, question: str, llm_backend: str = "groq", model_name: str = "meta-llama/llama-3.1-70b-versatile", max_iterations: int = 5, temperature: float = 0.3, auto_approve: bool = False, use_tools: bool = True) -> Dict[str, Any]:
        """
        Enhanced chat with tools integration for BeagleMind RAG system.
        
        Args:
            question: User's question or request
            llm_backend: Backend to use ("groq" or "ollama")
            model_name: Model to use for the backend
            max_iterations: Maximum number of tool calls to allow
            temperature: Temperature for model responses
            
        Returns:
            Dictionary with the conversation and results
        """
        try:
            # Determine how many results to fetch based on backend (keep small for Ollama)
            max_results = 3 if llm_backend.lower() == "ollama" else 5
            
            # Build initial context from search
            search_results = self.search(question, n_results=max_results, rerank=True)
            context_docs = self._build_context_docs_from_search(search_results, max_results)
            context = self._build_context_string(context_docs)
            
            # Get machine info for context
            machine_info = tool_registry.get_machine_info()
            
            # Create system prompt with essential rules and context
            system_prompt = prompt_generator.build_system_prompt_with_context(
                question, context, llm_backend, machine_info, use_tools
            )

            # Build messages with prior history in RAM
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self._get_history_messages())
            messages.append({
                "role": "user",
                "content": str(question) if question else "Hello, I need help with BeagleBoard development."
            })
            
            conversation = []
            tool_results = []
            
            # Build tool list only for Groq/OpenAI; Ollama must not have tool calling
            tools = None
            if llm_backend.lower() in ("groq", "openai"):
                base_tools = self.get_available_tools() if use_tools else []
                tools = base_tools + [self._retrieve_tool_def()]

            for iteration in range(max_iterations):
                # Get response using the specified backend
                if llm_backend.lower() == "groq":
                    response_content, tool_calls = llm_service.chat_with_groq(messages, model_name, temperature, tools)
                elif llm_backend.lower() == "openai":
                    response_content, tool_calls = llm_service.chat_with_openai(messages, model_name, temperature, tools)
                elif llm_backend.lower() == "ollama":
                    response_content, tool_calls = llm_service.chat_with_ollama(messages, model_name, temperature)
                else:
                    raise ValueError(f"Unsupported backend: {llm_backend}")
                
                # Ensure content is never null
                message_content = response_content or ""
                
                # Add the assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": message_content
                }
                
                if tool_calls:
                    assistant_message["tool_calls"] = [
                        {
                            "id": tc.get("id", f"call_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        } for i, tc in enumerate(tool_calls)
                    ]
                
                messages.append(assistant_message)
                
                conversation.append({
                    "role": "assistant",
                    "content": message_content,
                    "tool_calls": []
                })
                
                # Execute tools if requested
                if tool_calls:
                    for tool_call in tool_calls:
                        # Parse the tool call
                        function_name = tool_call["function"]["name"]
                        try:
                            function_args = json.loads(tool_call["function"]["arguments"])
                        except json.JSONDecodeError:
                            function_args = tool_service.parse_tool_arguments(tool_call["function"]["arguments"], function_name)
                        
                        # Execute tool with feedback using service
                        tool_result = tool_service.execute_tool_with_feedback(function_name, function_args, auto_approve)
                        
                        tool_results.append({
                            "tool": function_name,
                            "arguments": function_args,
                            "result": tool_result,
                            "requires_permission": function_name in ["write_file", "edit_file_lines"],
                            "user_approved": auto_approve if function_name in ["write_file", "edit_file_lines"] else None
                        })
                        
                        conversation[-1]["tool_calls"].append({
                            "function": function_name,
                            "arguments": function_args,
                            "result": tool_result
                        })
                        
                        # Add tool result to messages for next LLM call
                        tool_content = json.dumps(tool_result) if tool_result else "{}"
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id", f"call_{len(messages)}"),
                            "content": tool_content
                        })
                    
                    # Continue for follow-up response
                    continue
                else:
                    # No more tool calls, we're done
                    break
            
            # Prepare final response with source information
            sources = utils.prepare_sources_for_response(context_docs)
            
            # Record this turn in memory (user + assistant)
            try:
                self._record_user(question)
                self._record_assistant(conversation[-1]["content"] if conversation else "")
            except Exception:
                pass

            return {
                "success": True,
                "answer": conversation[-1]["content"] if conversation else "No response generated",
                "conversation": conversation,
                "tool_results": tool_results,
                "sources": sources,
                "iterations_used": iteration + 1,
                "search_info": {
                    "total_found": len(context_docs),
                    "backend_used": llm_backend,
                    "model_used": model_name
                }
            }
            
        except Exception as e:
            logger.error(f"Chat with tools failed: {e}")
            return {
                "success": False,
                "error": f"Chat failed: {str(e)}",
                "answer": f"I encountered an error while processing your request. Please try again. Error: {str(e)}"
            }


    def ask_question(self, question: str, search_strategy: str = "adaptive", 
                    n_results: int = 5, include_context: bool = False, model_name: str = "meta-llama/llama-3.1-70b-versatile", 
                    temperature: float = 0.3, llm_backend: str = "groq", use_tools: bool = True, auto_approve: bool = False) -> Dict[str, Any]:
        """Enhanced question answering with adaptive search strategies and smart tool integration"""
        # Use chat_with_tools by default; Ollama will still have no tool access internally
        if use_tools:
            logger.info(f"Using chat_with_tools for interactive question: {question[:50]}...")
            return self.chat_with_tools(
                question=question, 
                llm_backend=llm_backend, 
                model_name=model_name, 
                temperature=temperature,
                auto_approve=auto_approve,
                use_tools=(llm_backend.lower() in ("groq", "openai"))
            )
        
        # Fallback to traditional RAG approach for simple informational questions
        logger.info(f"Using traditional RAG for informational question: {question[:50]}...")
        return self._traditional_rag_response(question, search_strategy, n_results, include_context, model_name, temperature, llm_backend)
    
    def _traditional_rag_response(self, question: str, search_strategy: str, n_results: int, include_context: bool, model_name: str, temperature: float, llm_backend: str) -> Dict[str, Any]:
        """Traditional RAG response for informational queries"""
        max_results = 3 if llm_backend.lower() == "ollama" else n_results

        # Retrieval is the only context source: single retrieval call (no extra steps)
        search_results = self.search(question, n_results=max_results, rerank=True)

        # If still nothing, graceful LLM-only fallback
        if not (search_results and search_results.get('documents') and search_results['documents'] and search_results['documents'][0]):
            retrieval_note = ""
            if search_results and search_results.get('retrieval_ok') is False:
                retrieval_note = "Note: retrieval system not configured or unreachable. "

            # Include prior conversation turns in the fallback prompt
            history_lines = []
            for m in self._get_history_messages():
                if m["role"] == "user":
                    history_lines.append(f"User: {m['content']}")
                elif m["role"] == "assistant":
                    history_lines.append(f"Assistant: {m['content']}")
            history_block = ("Conversation so far:\n" + "\n".join(history_lines) + "\n\n") if history_lines else ""
            fallback_prompt = (
                "You are BeagleMind, a concise, reliable assistant for Beagleboard tasks.\n\n"
                "No repository context is available for this question. Provide a practical, step-by-step answer "
                "with a small code example when helpful. Keep it accurate and concise.\n\n"
                f"{history_block}Question: {question}\n\nAnswer:"
            )
            try:
                answer, used_backend = llm_service.call_llm_with_fallback(fallback_prompt, llm_backend, model_name, temperature)
                if used_backend is None:
                    raise RuntimeError(answer)
            except Exception as e:
                logger.error(f"LLM fallback failed: {e}")
                answer = "I couldn't generate an answer right now. Please try again."

            final_answer = (retrieval_note + answer) if retrieval_note else answer
            try:
                self._record_user(question)
                self._record_assistant(final_answer)
            except Exception:
                pass
            return {
                "answer": final_answer,
                "sources": [],
                "search_info": {
                    "strategy": search_strategy,
                    "question_types": None,
                    "filters": None,
                    "total_found": 0,
                    "used_fallback": True
                }
            }

        # Build context docs
        context_docs = self._build_context_docs_from_search(search_results, max_results)

        # Generate prompt with conversation history
        prompt = prompt_generator.generate_context_aware_prompt(question, context_docs, None)
        history_lines = []
        for m in self._get_history_messages():
            if m["role"] == "user":
                history_lines.append(f"User: {m['content']}")
            elif m["role"] == "assistant":
                history_lines.append(f"Assistant: {m['content']}")
        if history_lines:
            prompt = "Conversation so far:\n" + "\n".join(history_lines) + "\n\n---\n" + prompt

        # Call LLM
        try:
            answer, used_backend = llm_service.call_llm_with_fallback(prompt, llm_backend, model_name, temperature)
            if used_backend is None:
                raise RuntimeError(answer)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            answer = f"Error generating answer: {str(e)}"

        # Prepare sources
        sources = []
        for doc in context_docs:
            sources.append({
                "content": doc['text'],
                "file_name": doc['file_info'].get('name', 'Unknown'),
                "file_path": doc['file_info'].get('path', ''),
                "file_type": doc['file_info'].get('type', 'unknown'),
                "language": doc['file_info'].get('language', 'unknown'),
                "source_link": doc['metadata'].get('source_link'),
                "raw_url": doc['metadata'].get('raw_url'),
                "metadata": {
                    "chunk_index": doc['metadata'].get('chunk_index'),
                    "has_code": doc['metadata'].get('has_code', False),
                    "has_images": doc['metadata'].get('has_images', False),
                    "quality_score": doc['metadata'].get('content_quality_score')
                }
            })

        # Record turn
        try:
            self._record_user(question)
            self._record_assistant(answer)
        except Exception:
            pass

        return {
            "answer": answer,
            "sources": sources,
            "search_info": {
                "strategy": search_strategy,
                "question_types": None,
                "filters": None,
                "total_found": len(search_results.get('documents', [[]])[0]) if search_results else 0,
                "processed_count": len(context_docs)
            }
        }
    



    


