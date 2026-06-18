"""
Week 5: Agent Architecture Starter Template

Build an AI agent that answers TechCorp questions using:
- Gemini 2.5 Pro LLM (free tier via Google AI API)
- SQLite database queries
- Policy document retrieval

Complete the TODO sections marked below.
"""

import json
import sqlite3
import time
from typing import Dict, Any
import google.genai as genai
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


# TASK 1: Implement the Tool base class


class Tool:
    """Base class for tools the agent can call."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, **kwargs) -> str:
        """Execute the tool.

        TODO: This is implemented by subclasses.
        Each subclass should override this method.
        """
        raise NotImplementedError


# TASK 2: Implement EmployeeLookupTool


class EmployeeLookupTool(Tool):
    """Look up employee information from SQLite database."""

    def __init__(self, db_path: str):
        super().__init__("employee_lookup", "Find employee information by name or ID")
        self.db_path = db_path

    def execute(self, employee_name: str = None, employee_id: str = None) -> str:
        """Look up employee by name or ID.

        TODO: Query the employees table:
        1. Connect to SQLite database at self.db_path
        2. If employee_id is provided:
           - SELECT * FROM employees WHERE id = ?
        3. If employee_name is provided:
           - SELECT * FROM employees WHERE name LIKE ?
        4. Convert results to JSON and return
        5. If no results found, return "Employee not found"

        Args:
            employee_name: Name to search for (partial match ok)
            employee_id: ID to search for (exact match)

        Returns:
            JSON string with employee info or error message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if employee_id is not None:
                cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            elif employee_name is not None:
                cursor.execute("SELECT * FROM employees WHERE name LIKE ?", (f"%{employee_name}%",))
            else:
                conn.close()
                return "Employee not found"
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            conn.close()
            if not rows:
                return "Employee not found"
            results = [dict(zip(col_names, row)) for row in rows]
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Employee lookup error: {e}")
            return f"Error: {str(e)}"


# TASK 3: Implement PolicySearchTool


class PolicySearchTool(Tool):
    """Search policy documents by keyword."""

    def __init__(self):
        super().__init__("policy_search", "Search policy documents by keyword or topic")
        # TODO: Load data/documents.json
        with open("data/documents.json") as f:
            self.documents = json.load(f)

    def execute(self, query: str, limit: int = 5) -> str:
        """Search policies by keyword.

        TODO: Implement policy search:
        1. Load documents (from JSON file in data/ folder)
        2. Search documents by keyword match
        3. Return top-N matching documents
        4. Include title and snippet (first 500 chars) for each

        Args:
            query: Search term
            limit: Max results to return

        Returns:
            Formatted string with matching documents
        """
        try:
            keywords = query.lower().split()
            matches = [
                doc for doc in self.documents
                if any(kw in doc["content"].lower() or kw in doc["title"].lower() for kw in keywords)
            ]
            matches = matches[:limit]
            if not matches:
                return "No matching policy documents found."
            results = []
            for doc in matches:
                snippet = doc["content"][:500]
                results.append(f"**{doc['title']}**\n{snippet}")
            return "\n\n---\n\n".join(results)
        except Exception as e:
            logger.error(f"Policy search error: {e}")
            return f"Error: {str(e)}"


# TASK 4: Implement ExpenseQueryTool


class ExpenseQueryTool(Tool):
    """Query expense policies and approval limits."""

    def __init__(self):
        super().__init__("expense_query", "Query expense approval limits by role")
        # TODO: load data/policies.json into the documents attribute
        with open("data/policies.json") as f:
            self.policies = json.load(f)

    def execute(self, role: str) -> str:
        """Query expense approval limit for a given role.

        TODO: Implement expense lookup:
        1. Look up role in self.policies["expense"]["approval_limits"]
        2. Return: "Approval limit for {role}: ${amount}"
        3. If role not found, return "Role not found: {role}"

        Args:
            role: Employee role (ic1_ic2, ic3, manager, director, vp)

        Returns:
            String with approval limit for the given role
        """
        try:
            limits = self.policies["expense"]["approval_limits"]
            if role in limits:
                return f"Approval limit for {role}: ${limits[role]}"
            return f"Role not found: {role}"
        except Exception as e:
            logger.error(f"Expense query error: {e}")
            return f"Error: {str(e)}"


# TASK 5: Implement the Agent class


class Agent:
    """AI agent that answers questions using Gemini LLM + tools."""

    def __init__(self, db_path: str, api_key: str = None):
        """Initialize the agent.

        TODO:
        1. Get API key from parameter or GOOGLE_API_KEY environment variable
        2. Raise ValueError if no API key provided
        3. Initialize Google GenAI client with api_key
        4. Initialize all tools (EmployeeLookup, PolicySearch, ExpenseQuery)
        5. Initialize token and cost tracking variables

        Args:
            db_path: Path to SQLite database
            api_key: Google AI API key (or use GOOGLE_API_KEY env var)
        """
        self.db_path = db_path
        self.api_key = api_key or GOOGLE_API_KEY

        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. Get free key at: "
                "https://aistudio.google.com/app/apikey"
            )

        # TODO: Initialize Google GenAI client
        # self.client = genai.Client(api_key=self.api_key)
        self.client = genai.Client(api_key=self.api_key)

        # TODO: Initialize tools dictionary
        # self.tools = {
        #     "employee_lookup": EmployeeLookupTool(db_path),
        #     "policy_search": PolicySearchTool(),
        #     "expense_query": ExpenseQueryTool(),
        # }
        self.tools = {
            "employee_lookup": EmployeeLookupTool(db_path),
            "policy_search": PolicySearchTool(),
            "expense_query": ExpenseQueryTool(),
        }

        # TODO: Initialize metrics
        # self.token_count = 0
        # self.total_cost = 0.0
        # self.queries_run = 0
        self.token_count = 0
        self.total_cost = 0.0
        self.queries_run = 0

    def _build_system_prompt(self, user_role: str) -> str:
        """Build system prompt describing available tools.

        TODO: Create a prompt that:
        1. Describes the agent's purpose
        2. Lists all available tools with descriptions
        3. Explains how to use them
        4. Sets the user's role context

        Returns:
            System prompt string
        """
        return (
            f"You are a TechCorp assistant. Answer employee questions using the tools below.\n"
            f"User role: {user_role}\n\n"
            f"Available tools:\n"
            f"- employee_lookup: Find employee information by name or ID\n"
            f"  Args: employee_name=<name> OR employee_id=<id>\n"
            f"- policy_search: Search policy documents by keyword or topic\n"
            f"  Args: query=<search term>\n"
            f"- expense_query: Query expense approval limits by role\n"
            f"  Args: role=<ic1_ic2|ic3|manager|director|vp>\n\n"
            f"To use a tool, respond with:\n"
            f"TOOL: <tool_name>\n"
            f"ARGS: <argument>=<value>\n\n"
            f"Only call one tool at a time. After receiving tool results, provide a clear final answer."
        )

    def query(self, user_query: str, user_role: str = "engineer") -> Dict[str, Any]:
        """Answer a question using LLM + tools.

        TODO: Implement the reasoning loop:

        1. Call _build_system_prompt(user_role) to build the system prompt

        2. Call Gemini LLM with system prompt + user question
           - self.client.models.generate_content(model="gemini-2.5-pro", ...)

        3. Parse LLM response to identify tool calls
           - Check if response mentions any tool names
           - Extract parameters from response

        4. Execute tools with extracted parameters
           - tool.execute() with parameters
           - Collect results

        5. Synthesize final answer
           - Pass tool results back to LLM
           - Get final answer

        6. Track tokens and cost
           - Count tokens in request/response
           - Calculate cost: (tokens / 1_000_000) * rate
           - Update totals

        Args:
            user_query: The question to answer
            user_role: User's role (for access control in future weeks)

        Returns:
            Dict with keys:
            - "answer": str - the response
            - "tokens_used": int - total tokens
            - "cost": float - cost in dollars
            - "role": str - user role
        """
        logger.info(f"Processing query: {user_query}")
        system_prompt = self._build_system_prompt(user_role)

        first_response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_query,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        first_text = first_response.text
        usage1 = first_response.usage_metadata
        input_tokens_1 = getattr(usage1, "prompt_token_count", 0) or 0
        output_tokens_1 = getattr(usage1, "candidates_token_count", 0) or 0

        input_tokens_2 = 0
        output_tokens_2 = 0
        final_answer = first_text

        tool_name = None
        for name in self.tools:
            if f"TOOL: {name}" in first_text:
                tool_name = name
                break

        if tool_name:
            args = {}
            for line in first_text.splitlines():
                if line.strip().startswith("ARGS:"):
                    arg_str = line.split("ARGS:", 1)[1].strip()
                    if "=" in arg_str:
                        key, _, val = arg_str.partition("=")
                        args[key.strip()] = val.strip()
            tool_result = self.tools[tool_name].execute(**args)

            synthesis_prompt = (
                f"User question: {user_query}\n\n"
                f"Tool result:\n{tool_result}\n\n"
                f"Provide a clear, helpful answer based on the tool result."
            )
            second_response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=synthesis_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            final_answer = second_response.text
            usage2 = second_response.usage_metadata
            input_tokens_2 = getattr(usage2, "prompt_token_count", 0) or 0
            output_tokens_2 = getattr(usage2, "candidates_token_count", 0) or 0

        total_input = input_tokens_1 + input_tokens_2
        total_output = output_tokens_1 + output_tokens_2
        cost = self._estimate_query_cost(total_input, total_output)

        self.token_count += total_input + total_output
        self.total_cost += cost
        self.queries_run += 1

        return {
            "answer": final_answer,
            "tokens_used": total_input + total_output,
            "cost": cost,
            "role": user_role,
        }

    def _estimate_query_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on tokens.

        Gemini 2.5 Pro pricing:
        - Input: $0.075 per 1M tokens
        - Output: $0.3 per 1M tokens
        """
        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.3
        return input_cost + output_cost

    def get_metrics(self) -> Dict[str, Any]:
        """Return performance metrics.

        TODO: Return dict with:
        - total_queries: number of queries processed
        - total_tokens: cumulative tokens used
        - total_cost: cumulative cost in dollars
        - avg_cost_per_query: average cost per query
        """
        # TODO: implement
        return {
            "total_queries": self.queries_run,
            "total_tokens": self.token_count,
            "total_cost": self.total_cost,
            "avg_cost_per_query": self.total_cost / self.queries_run if self.queries_run > 0 else 0.0,
        }


# TASK 6: Test your implementation

if __name__ == "__main__":
    """Quick test of agent functionality."""
    import sys

    try:
        # Initialize agent
        agent = Agent("data/techcorp.db")
        print("Agent initialized successfully\n")

        test_queries = [
            "Find information about Brian Yang",
            "Who is Kim Martinez?",
            "Look up employee Tyler Miller",
            "What is the travel policy?",
            "What are the employee benefits?",
            "What is the PTO policy?",
            "What is the code of conduct?",
            "What is the expense approval limit for a manager?",
            "What is the expense approval limit for a director?",
            "What is the expense approval limit for a vp?",
        ]

        for i, q in enumerate(test_queries, 1):
            print(f"--- Query {i}/10 ---")
            print(f"Q: {q}")
            result = agent.query(q)
            print(f"Answer: {result['answer']}")
            print(f"Tokens: {result['tokens_used']}  |  Cost: ${result['cost']:.6f}\n")
            if i < len(test_queries):
                time.sleep(30)

        # Check metrics
        metrics = agent.get_metrics()
        print("=== Final Metrics ===")
        print(f"Total queries:        {metrics['total_queries']}")
        print(f"Total tokens:         {metrics['total_tokens']}")
        print(f"Total cost:           ${metrics['total_cost']:.6f}")
        print(f"Avg cost per query:   ${metrics['avg_cost_per_query']:.6f}")

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Error during test")
        sys.exit(1)
