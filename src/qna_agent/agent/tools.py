"""OpenAI function/tool definitions for the agent."""

from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search for relevant information in the knowledge base. "
            "Use this to find documents related to a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_knowledge_files",
            "description": "List all available files in the knowledge base. "
            "Use this to see what documents are available.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_knowledge_file",
            "description": "Read the contents of a specific file from the knowledge base. "
            "Use this to get the full content of a document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to read",
                    }
                },
                "required": ["filename"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a helpful QnA assistant with access to a knowledge base.
Your role is to answer questions using information from the available documents.

Guidelines:
1. When asked a question, first search the knowledge base for relevant information
2. If you find relevant documents, read them to get the full context
3. Be concise but thorough in your responses
4. If you cannot find relevant information in the knowledge base, say so clearly
5. ALWAYS end your response with a sources section listing all files you read:

   Sources: filename1.md, filename2.md

Available tools:
- search_knowledge_base: Search for relevant documents
- list_knowledge_files: See all available documents
- read_knowledge_file: Read a specific document's contents
"""
