import os
import json
import asyncio
import google.generativeai as genai
from backend.config import settings

class GeminiService:
    """Service to process raw code diffs and perform code reviews using Gemini 1.5 Flash."""

    def __init__(self):
        # Configure the Google generative AI library with loaded API key
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key":
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-1.5-flash"

    async def analyze_diff(self, diff_text: str) -> list:
        """Sends raw PR diff output to Gemini, asking it to audit the code changes and produce JSON comments.

        Returns a parsed list of review comments: file_path, line_number, severity, category, and comment text.
        Runs non-blocking in a thread pool executor.
        """
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key":
            # Return dummy reviews in dry-run/unconfigured states
            return [
                {
                    "file_path": "backend/main.py",
                    "line_number": 5,
                    "severity": "minor",
                    "category": "style",
                    "comment": "Gemini API key is unconfigured. This is an auto-generated dry run placeholder review."
                }
            ]

        # Detailed system instruction to structure Gemini's output
        system_instruction = (
            "You are an expert software engineer and security auditor. Analyze the provided git diff text. "
            "Identify bugs, security vulnerabilities (e.g. OWASP top 10), performance slowdowns, "
            "and significant code smells. Provide your feedback strictly in a JSON array. "
            "Each item in the array must have the following fields:\n"
            "- 'file_path': The path to the file being edited\n"
            "- 'line_number': The specific line number in the new code (right side) where this issue exists (integer)\n"
            "- 'severity': 'critical', 'major', 'minor', or 'info'\n"
            "- 'category': 'bug', 'security', 'performance', or 'style'\n"
            "- 'comment': A concise, actionable explanation of the issue with correction recommendations\n"
            "Do not wrap your output in markdown code blocks. Output raw JSON only."
        )

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )

        prompt = f"Analyze the following git diff and output the code review issues:\n\n{diff_text}"
        
        # Call the model via thread executor to prevent blocking FastAPI's event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback if the AI returned non-JSON structure despite the mime_type directive
            return [
                {
                    "file_path": "unknown",
                    "line_number": None,
                    "severity": "major",
                    "category": "bug",
                    "comment": f"Failed to parse Gemini response as JSON. Original output: {response.text}"
                }
            ]
