"""Gradio interface wiring for the AI PDF Translator."""

from __future__ import annotations

import gradio as gr

from .translation_service import translate_pdf


def build_interface() -> gr.Blocks:
    language_choices = ["English", "Spanish", "French", "German", "Italian", "Portuguese"]

    with gr.Blocks(title="AI PDF Translator") as demo:
        gr.Markdown(
            """
            # AI PDF Translator
            Upload a PDF and translate it with OpenAI. Default translation: English → Spanish.
            """
        )

        with gr.Row():
            pdf_input = gr.File(label="PDF", file_types=[".pdf"], type="filepath")
            with gr.Column():
                source = gr.Dropdown(language_choices, value="English", label="Source language")
                target = gr.Dropdown(language_choices, value="Spanish", label="Target language")

        translate_button = gr.Button("Translate PDF")
        output = gr.Textbox(
            label="Translated text",
            placeholder="Translation appears here",
            lines=20,
        )
        download = gr.File(label="Download translated PDF")

        translate_button.click(
            fn=translate_pdf,
            inputs=[pdf_input, source, target],
            outputs=[output, download],
        )

    return demo


__all__ = ["build_interface"]
