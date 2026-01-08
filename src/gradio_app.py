import gradio as gr
import logging
import re
from typing import List, Tuple

from .qa_system import QASystem
from . import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]

OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "o1-preview",
    "o1-mini",
]

OLLAMA_MODELS = [
    "qwen3:1.7b",
]

LLM_BACKENDS = ["groq", "openai", "ollama"]


class GradioRAGApp:
    def __init__(self, collection_name: str = None):
        """Initialize the Gradio RAG application"""
        self.collection_name = collection_name or config.COLLECTION_NAME
        self.retrieval_system = None
        self.qa_system = None

        self.selected_backend = LLM_BACKENDS[0]      # default: groq
        self.selected_model = GROQ_MODELS[0]         # default: first groq model
        self.temperature = 0.3

        self.setup_system()

    def get_models_for_backend(self, backend_name: str):
        """
        Get available models for a given backend.
        Prefer QA system's info, else fall back to static lists.
        """
        # Try delegate to QA system if it exposes models
        if self.qa_system is not None:
            if hasattr(self.qa_system, "get_models_for_backend"):
                try:
                    models = self.qa_system.get_models_for_backend(backend_name)
                    if models:
                        return models
                except Exception as e:
                    logger.warning(f"qa_system.get_models_for_backend failed: {e}")
            if hasattr(self.qa_system, "models_by_backend"):
                models = self.qa_system.models_by_backend.get(backend_name, [])
                if models:
                    return models

        # Fallback: local constants
        if backend_name == "groq":
            return GROQ_MODELS
        if backend_name == "openai":
            return OPENAI_MODELS
        if backend_name == "ollama":
            return OLLAMA_MODELS
        return []

    def setup_system(self):
        """Initialize the RAG system components"""
        try:
            logger.info("Initializing RAG system...")
            self.qa_system = QASystem(self.collection_name)
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise

    def clean_llm_response(self, response: str) -> str:
        """Clean LLM response by removing thinking tags and extracting actual answer"""
        if not response:
            return response

        cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<thinking>.*?</thinking>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        return cleaned

    def format_sources(self, sources: List[dict]) -> str:
        """Format source information as markdown with enhanced details, filtering out duplicates"""
        if not sources:
            return "No sources found."

        unique_sources = self._filter_duplicate_sources(sources)
        if not unique_sources:
            return "No unique sources found."

        markdown_sources = "## Sources & References\n\n"

        for i, source in enumerate(unique_sources, start=1):
            markdown_sources += f"### Source {i}\n"

            file_name = source.get("file_name", "Unknown")
            file_type = source.get("file_type", "unknown")
            language = source.get("language", "unknown")

            source_link = source.get("source_link", "")
            markdown_sources += f"**File:** `{file_name}` ({file_type})\n"
            if language != "unknown":
                markdown_sources += f"**Language:** {language}\n"
            if source_link:
                markdown_sources += f"**Source Link:** [{file_name}]({source_link})\n"

            metadata = source.get("metadata", {})
            indicators = []
            if metadata.get("has_code"):
                indicators.append("Code")
            if metadata.get("has_images"):
                indicators.append("Images")

            if indicators:
                markdown_sources += f"**Contains:** {' | '.join(indicators)}\n"

        return markdown_sources

    def _filter_duplicate_sources(self, sources: List[dict]) -> List[dict]:
        """Filter out duplicate sources based on content and metadata"""
        unique_sources = []
        seen_content = set()
        seen_file_paths = set()

        for source in sources:
            content = source.get("content", "").strip()
            file_name = source.get("file_name", "")
            file_path = source.get("file_path", "")

            if content and content in seen_content:
                continue

            file_identifier = f"{file_name}:{file_path}"
            if file_identifier in seen_file_paths:
                continue

            is_duplicate = False
            for existing_content in seen_content:
                if self._are_contents_similar(content, existing_content):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_sources.append(source)
                if content:
                    seen_content.add(content)
                seen_file_paths.add(file_identifier)

        return unique_sources

    def _are_contents_similar(self, content1: str, content2: str, similarity_threshold: float = 0.9) -> bool:
        """Check if two content strings are very similar (likely duplicates)"""
        if not content1 or not content2:
            return False

        if content1 == content2:
            return True

        shorter, longer = (content1, content2) if len(content1) < len(content2) else (content2, content1)

        if len(shorter) < 100:
            return shorter in longer

        overlap = len(set(shorter.split()) & set(longer.split()))
        shorter_words = len(shorter.split())

        if shorter_words > 0:
            similarity = overlap / shorter_words
            return similarity >= similarity_threshold

        return False

    def format_search_info(self, search_info: dict) -> str:
        """Format search information for display"""
        if not search_info:
            return ""

        info_text = "## Search Details\n\n"

        strategy = search_info.get("strategy", "unknown")
        info_text += f"**Strategy:** {strategy.title()}\n"

        question_types = search_info.get("question_types", [])
        if question_types:
            info_text += f"**Question Types:** {', '.join(question_types)}\n"

        filters = search_info.get("filters", {})
        if filters:
            filter_items = [f"{key}: {value}" for key, value in filters.items()]
            info_text += f"**Filters Applied:** {', '.join(filter_items)}\n"

        total_found = search_info.get("total_found", 0)
        reranked_count = search_info.get("reranked_count", 0)
        info_text += f"**Documents Found:** {total_found}\n"
        info_text += f"**After Reranking:** {reranked_count}\n"

        return info_text

    def get_dynamic_suggestions(self) -> List[str]:
        """Get dynamic question suggestions from QA system"""
        try:
            return self.qa_system.get_question_suggestions(n_suggestions=8)
        except Exception as e:
            logger.warning(f"Could not get dynamic suggestions: {e}")
            return [
                "What is this repository about?",
                "How does the system work?",
                "What are the main features?",
                "What technologies are used?",
                "How do I set it up?",
                "Show me code examples",
                "What are best practices?",
                "How to troubleshoot issues?",
            ]

    def chat_with_bot(
        self,
        message: str,
        history: list,
        model_name: str,
        temperature: float,
        llm_backend: str,
        search_strategy: str = "adaptive",
    ) -> Tuple[str, List[Tuple[str, str]], str, str]:
        if not message.strip():
            return "", history, "Please enter a question.", ""

        try:
            if not history:
                try:
                    self.qa_system.start_conversation()
                except Exception:
                    pass

            result = self.qa_system.ask_question(
                message,
                search_strategy=search_strategy,
                model_name=model_name,
                temperature=temperature,
                llm_backend=llm_backend,
            )
            raw_answer = result.get("answer", "Sorry, I couldn't generate an answer.")
            sources = result.get("sources", [])
            search_info = result.get("search_info", {})

            cleaned_answer = self.clean_llm_response(raw_answer)
            formatted_answer = f"## Answer\n\n{cleaned_answer}"

            question_types = search_info.get("question_types", [])
            if question_types:
                formatted_answer += f"\n\n---\n**Detected Question Types:** {', '.join(question_types)}"

            formatted_answer += f"\n**LLM Backend:** {llm_backend.upper()}"

            history.append((message, formatted_answer))

            sources_markdown = self.format_sources(sources)
            search_info_text = self.format_search_info(search_info)

            return "", history, sources_markdown, search_info_text

        except Exception as e:
            error_message = f"Error: {str(e)}"
            history.append((message, error_message))
            return "", history, "Error occurred while processing your question.", ""

    def clear_chat(self):
        """Clear chat history and sources"""
        try:
            self.qa_system.reset_conversation()
        except Exception:
            pass
        return [], "Chat cleared. Ask me anything!"

    def generate_code_file(self, query: str, file_type: str, model_name: str, temperature: float, llm_backend: str) -> Tuple[str, str, str]:
        """Generate code file (stub implementation)"""
        return "", "", "Code generation not implemented"

    # ---- code generation methods remain same (shortened here, paste your existing ones) ----
    # generate_code_file, _get_groq_response, _get_ollama_response,
    # _get_openai_response, _generate_intelligent_filename,
    # _fallback_filename_generation
    # (yahin pe tum apna existing code as-is rakh sakti ho)

    # ----------------- UI -----------------

    def create_interface(self):
        """Create and configure the Gradio interface with tabs for chatbot and code generation"""

        css = """
        .gradio-container {
            max-width: 1800px !important;
            margin: auto;
            padding: 20px;
        }
        #chatbot {
            height: 600px !important;
        }
        .sources-container {
            height: 600px !important;
            overflow-y: auto !important;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        .code-container {
            height: 500px !important;
            overflow-y: auto !important;
            font-family: 'Courier New', monospace;
        }
        """

        # Gradio 6: theme/css ko launch() par pass karenge
        with gr.Blocks(title="RAG System & Code Generator") as interface:
            gr.Markdown("# Multi-Backend RAG System with Code Generation")

            with gr.Tabs():
                # Tab 1: Chatbot
                with gr.TabItem("💬 RAG Chatbot"):
                    with gr.Row():
                        with gr.Column(scale=5, min_width=800):
                            chatbot = gr.Chatbot(
                                value=[],
                                elem_id="chatbot",
                                show_label=False,
                                container=True,
                                
                            )

                            msg_input = gr.Textbox(
                                placeholder="Ask a question about the repository...",
                                show_label=False,
                                scale=5,
                                container=False,
                            )

                            with gr.Row():
                                submit_btn = gr.Button("Send", variant="primary", scale=4)
                                clear_btn = gr.Button("Clear Chat", variant="secondary", scale=1)

                        with gr.Column(scale=4, min_width=600):
                            gr.Markdown("### Sources & References")
                            sources_display = gr.Markdown(
                                value="Sources will appear here after asking a question.",
                                elem_classes=["sources-container"],
                            )

                    # Shared controls for chatbot
                    with gr.Row():
                        chat_backend_dropdown = gr.Dropdown(
                            choices=LLM_BACKENDS,
                            value=self.selected_backend,
                            label="LLM Backend",
                            interactive=True,
                        )

                        # safe init: ensure choices non-empty
                        init_chat_models = self.get_models_for_backend(self.selected_backend)
                        if not init_chat_models:
                            init_chat_models = []

                        chat_model_dropdown = gr.Dropdown(
                            choices=init_chat_models,
                            value=init_chat_models[0] if init_chat_models else None,
                            label="Model",
                            interactive=True,
                            allow_custom_value=True,
                        )

                        chat_temp_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=self.temperature,
                            step=0.01,
                            label="Temperature",
                            interactive=True,
                        )

                # Tab 2: Code Generation
                with gr.TabItem("🔧 Code Generator"):
                    gr.Markdown(
                        "### Generate Python or Shell scripts based on your requirements using RAG-enhanced context"
                    )

                    with gr.Row():
                        with gr.Column(scale=2):
                            code_query_input = gr.Textbox(
                                placeholder="Describe the code you want to generate (e.g., 'Create a script to backup files')",
                                label="Code Generation Request",
                                lines=3,
                            )

                            file_type_radio = gr.Radio(
                                choices=["python", "shell"],
                                value="python",
                                label="File Type",
                                interactive=True,
                            )

                            generate_btn = gr.Button("Generate Code", variant="primary", size="lg")

                            status_output = gr.Textbox(
                                label="Status",
                                interactive=False,
                                lines=2,
                            )

                        with gr.Column(scale=3):
                            filename_output = gr.Textbox(
                                label="Generated Filename",
                                interactive=False,
                            )

                            code_output = gr.Code(
                                label="Generated Code",
                                language="python",
                                elem_classes=["code-container"],
                                interactive=False,
                            )

                            download_btn = gr.DownloadButton(
                                label="Download File",
                                variant="secondary",
                            )

                    # Shared controls for code generation
                    with gr.Row():
                        code_backend_dropdown = gr.Dropdown(
                            choices=LLM_BACKENDS,
                            value=self.selected_backend,
                            label="LLM Backend",
                            interactive=True,
                        )

                        init_code_models = self.get_models_for_backend(self.selected_backend)
                        if not init_code_models:
                            init_code_models = []

                        code_model_dropdown = gr.Dropdown(
                            choices=init_code_models,
                            value=init_code_models[0] if init_code_models else None,
                            label="Model",
                            interactive=True,
                            allow_custom_value=True,
                        )

                        code_temp_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=self.temperature,
                            step=0.01,
                            label="Temperature",
                            interactive=True,
                        )

            # ---- helper fns inside Blocks ----

            def update_chat_models(backend):
                models = self.get_models_for_backend(backend)
                if not models:
                    models = []
                return gr.update(choices=models, value=models[0] if models else None)

            def update_code_models(backend):
                models = self.get_models_for_backend(backend)
                if not models:
                    models = []
                return gr.update(choices=models, value=models[0] if models else None)

            def update_code_language(file_type):
                language = "python" if file_type == "python" else "bash"
                return gr.update(language=language)

            chat_backend_dropdown.change(
                fn=update_chat_models,
                inputs=[chat_backend_dropdown],
                outputs=[chat_model_dropdown],
            )

            def submit_message(message, history, backend, model_name, temperature):
                self.selected_backend = backend
                self.selected_model = model_name
                self.temperature = temperature
                return self.chat_with_bot(message, history, model_name, temperature, backend)

            submit_btn.click(
                fn=submit_message,
                inputs=[msg_input, chatbot, chat_backend_dropdown, chat_model_dropdown, chat_temp_slider],
                outputs=[msg_input, chatbot, sources_display],
            )

            msg_input.submit(
                fn=submit_message,
                inputs=[msg_input, chatbot, chat_backend_dropdown, chat_model_dropdown, chat_temp_slider],
                outputs=[msg_input, chatbot, sources_display],
            )

            clear_btn.click(
                fn=self.clear_chat,
                inputs=[],
                outputs=[chatbot, sources_display],
            )

            code_backend_dropdown.change(
                fn=update_code_models,
                inputs=[code_backend_dropdown],
                outputs=[code_model_dropdown],
            )

            file_type_radio.change(
                fn=update_code_language,
                inputs=[file_type_radio],
                outputs=[code_output],
            )

            def handle_code_generation(query, file_type, backend, model_name, temperature):
                generated_code, filename, status = self.generate_code_file(
                    query, file_type, model_name, temperature, backend
                )
                if generated_code and filename:
                    import tempfile
                    import os

                    file_path = os.path.join(tempfile.gettempdir(), filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(generated_code)
                    return generated_code, filename, status, gr.update(value=file_path, visible=True)
                else:
                    return generated_code, filename, status, gr.update(visible=False)

            generate_btn.click(
                fn=handle_code_generation,
                inputs=[code_query_input, file_type_radio, code_backend_dropdown, code_model_dropdown, code_temp_slider],
                outputs=[code_output, filename_output, status_output, download_btn],
            )

        # css/theme ko launch me pass karenge
        interface.css = css
        interface.theme = gr.themes.Soft()
        return interface

    def launch(self, share=False, server_name="127.0.0.1", server_port=7860):
        """Launch the Gradio interface"""
        try:
            interface = self.create_interface()
            logger.info(f"Launching Gradio app on {server_name}:{server_port}")

            interface.launch(
                share=False,   
                server_name="127.0.0.1",
                server_port=7860,
                show_error=True,
            )
        except Exception as e:
            logger.error(f"Failed to launch Gradio app: {e}")
            raise


def main():
    """Main function to run the Gradio app"""
    try:
        app = GradioRAGApp()
        app.launch(server_name="0.0.0.0", server_port=7860)
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Launching Gradio app...")
    main()