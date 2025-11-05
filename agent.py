"""
Finance Agent - Anthropic Technical Content Engineer Assessment

A finance agent that uses Claude to look up stock prices and perform precise
mathematical calculations through tool use.

Key features:
- Multi-turn agentic loop with tool execution
- Portfolio calculations (multiple stocks in one call)
- Self-describing tool results for better context
- Parallel tool use optimization
"""

import json
import math
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

# =============================================================================
# Configuration & Setup
# =============================================================================

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError(
        "ANTHROPIC_API_KEY not found. Please set it in your .env file or environment variables. "
        "See .env.example for the template."
    )
if not api_key.startswith("sk-ant-"):
    raise ValueError(
        "Invalid ANTHROPIC_API_KEY format. API key should start with 'sk-ant-'. "
        "Please check your .env file or environment variables."
    )

client = Anthropic(api_key=api_key)

# Claude API configuration constants
CLAUDE_MODEL = "claude-3-5-haiku-20241022"
MAX_TOKENS = 1024
TEMPERATURE = 0.0

# Centralized stock price data - add new stocks here to extend the agent's capabilities
STOCK_PRICES: Dict[str, Dict[str, Any]] = {
    "aapl": {"price": 195.50, "name": "Apple"},
    "msft": {"price": 425.30, "name": "Microsoft"},
    "nvda": {"price": 875.20, "name": "NVIDIA"},
    "goog": {"price": 162.75, "name": "Alphabet (Google)"},
    "googl": {"price": 162.75, "name": "Alphabet (Google)"},
    "amzn": {"price": 185.40, "name": "Amazon"},
    "meta": {"price": 520.80, "name": "Meta (Facebook)"},
    "tsla": {"price": 245.60, "name": "Tesla"},
}

# System prompt that defines the agent's behavior and tool usage guidelines
SYSTEM_PROMPT = """You are a helpful finance assistant that can look up stock prices and perform precise calculations.

Always use the available tools for:
- Stock prices: Use calculate_portfolio_value to look up stock prices. For a single stock price, use quantity=1 (e.g., [{"ticker": "tsla", "quantity": 1}])
- Portfolio calculations: Use calculate_portfolio_value when asked about buying multiple stocks or calculating portfolio value
- Math calculations: Use calculate for any numerical computations to ensure precision

EFFICIENCY TIP - Parallel Tool Calls:
You can make multiple tool calls in a single response. When you identify operations that are independent (don't depend on each other's results), consider calling them in parallel to reduce the number of turns.

Example: For "173 * 3232 + 342 / 72.1", both the multiplication and division can be done in parallel since they're independent, then you can add the results.

When answering questions:
- For single stock price queries, use calculate_portfolio_value with [{"ticker": "XXX", "quantity": 1}]
- For portfolio questions (e.g., "buy 15 shares of tesla and 24 shares of google"), use calculate_portfolio_value with ALL stocks in a single call
- CRITICAL: Your final response MUST be ONLY valid JSON with no additional text before or after
- Use this exact format:
{"result": <number or string>, "explanation": "<brief optional explanation>"}

For numerical answers (stock prices, calculations), put just the number in "result".
For conversational questions (like asking about capabilities), put a text response in "result".
Do not include any commentary, just the JSON object."""


# =============================================================================
# Tool Functions
# =============================================================================


def calculate_portfolio_value(stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get stock prices and calculate portfolio values.
    
    Can be used for single stock lookups (quantity=1) or multiple stocks.

    Args:
        stocks: List of dicts, each with 'ticker' (str) and 'quantity' (int/float).
                For single stock price, use [{"ticker": "xxx", "quantity": 1}]

    Returns:
        Dict with breakdown per stock (including price per share) and total value

    Raises:
        KeyError: If any ticker is not found
    """
    breakdown = []
    total_value = 0.0

    for stock in stocks:
        ticker = stock["ticker"].lower()
        quantity = stock["quantity"]

        if ticker not in STOCK_PRICES:
            raise KeyError(f"Ticker '{ticker}' not found in available stocks")

        price = STOCK_PRICES[ticker]["price"]
        value = price * quantity

        breakdown.append(
            {
                "ticker": ticker,
                "name": STOCK_PRICES[ticker]["name"],
                "price": price,
                "quantity": quantity,
                "value": value,
            }
        )
        total_value += value

    return {"breakdown": breakdown, "total_value": total_value}


def calculate(op: str, a: float, b: float) -> Dict[str, Any]:
    """
    Perform a binary mathematical operation.

    Args:
        op: Operation to perform (+, -, *, /, **, log)
        a: First operand (left side, or base for **, or value for log)
        b: Second operand (right side, or exponent for **, or base for log)

    Returns:
        Dict with operation details and result for better context

    Raises:
        ValueError: If operation is not supported
        ZeroDivisionError: If division by zero
        ValueError: If logarithm with invalid base
    """
    match op:
        case "+":
            result = a + b
        case "-":
            result = a - b
        case "*":
            result = a * b
        case "/":
            if b == 0:
                raise ZeroDivisionError("Division by zero")
            result = a / b
        case "**":
            result = a**b
        case "log":
            if b <= 0 or b == 1 or a <= 0:
                raise ValueError(f"Invalid logarithm: log({a}, {b})")
            result = math.log(a, b)
        case _:
            raise ValueError(f"Unsupported operation: {op}")

    return {"operation": op, "a": a, "b": b, "result": result}


# =============================================================================
# Tool Specifications
# =============================================================================

_portfolio_ticker_names = ", ".join(
    ["{} ({})".format(t, d["name"]) for t, d in STOCK_PRICES.items()]
)

calculate_portfolio_value_spec = {
    "name": "calculate_portfolio_value",
    "description": (
        "Get stock prices and calculate portfolio values. Use this for ANY stock price lookup - for a single stock, "
        "use quantity=1 (e.g., [{{\"ticker\": \"tsla\", \"quantity\": 1}}]). "
        "For multiple stocks, include all stocks in a single call. "
        f"Available tickers: {_portfolio_ticker_names}. Returns detailed breakdown with price per share and total value."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "stocks": {
                "type": "array",
                "description": "Array of stocks to calculate. Each item should have 'ticker' and 'quantity' fields.",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol (lowercase, e.g., 'tsla', 'goog')",
                        },
                        "quantity": {
                            "type": "number",
                            "description": "Number of shares to buy",
                        },
                    },
                    "required": ["ticker", "quantity"],
                },
            }
        },
        "required": ["stocks"],
    },
}

calculate_spec = {
    "name": "calculate",
    "description": "Performs precise mathematical calculations. Supports binary operations on two numbers. Returns a JSON object with the operation, operands, and result for clear context.",
    "input_schema": {
        "type": "object",
        "properties": {
            "op": {
                "type": "string",
                "description": "The operation: '+' (add), '-' (subtract), '*' (multiply), '/' (divide), '**' (exponentiation/power), 'log' (logarithm)",
            },
            "a": {
                "type": "number",
                "description": "First number. For basic math (+, -, *, /): left operand. For '**': base. For 'log': the value. For sqrt, use '**' with a as the number and b as 0.5.",
            },
            "b": {
                "type": "number",
                "description": "Second number. For basic math (+, -, *, /): right operand. For '**': exponent. For 'log': the base (use 2.718281828459045 for natural log).",
            },
        },
        "required": ["op", "a", "b"],
    },
}


# =============================================================================
# Helper Functions
# =============================================================================


def parse_json_response(text: str) -> Dict[str, Any]:
    """
    Parse JSON from Claude's response.
    
    With proper prompting (system prompt specifies JSON format), Claude should
    return pure JSON. This function handles JSON parsing with a fallback if the response is not pure JSON.

    Args:
        text: The response text that should contain JSON

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If no valid JSON found
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: try to find and parse JSON object if there's extra text
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(text[start_idx : end_idx + 1])
            except json.JSONDecodeError:
                pass
        raise json.JSONDecodeError("No valid JSON found in response", text, 0)


def call_claude(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None):
    """
    Call Claude API with tool use support.

    Args:
        messages: Conversation history
        tools: List of tool specifications (defaults to empty list)

    Returns:
        API response with content blocks
    """
    if tools is None:
        tools = []

    return client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=messages,
    )


# =============================================================================
# Main Agent
# =============================================================================


def execute_tool_call(tool_call: Any) -> Dict[str, Any]:
    """
    Execute a single tool call based on its name and input.

    Args:
        tool_call: Tool call object with 'name' and 'input' attributes

    Returns:
        Dict result from the tool execution

    Raises:
        ValueError: If tool name is unknown or required parameters are missing
    """
    tool_name = getattr(tool_call, "name", None)
    tool_input = getattr(tool_call, "input", {})

    if tool_name == "calculate_portfolio_value":
        return calculate_portfolio_value(tool_input.get("stocks", []))
    elif tool_name == "calculate":
        op = tool_input.get("op")
        a = tool_input.get("a")
        b = tool_input.get("b")

        # Validate all required parameters are present
        if op is None or a is None or b is None:
            raise ValueError(
                f"Missing required parameters for calculate: op={op}, a={a}, b={b}"
            )

        return calculate(op, a, b)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def finance_agent(prompt: str) -> None:
    """
    Agent loop that handles multi-turn tool use to answer finance and math questions.

    The agent will:
    1. Send the user prompt to Claude with available tools
    2. Execute any tool calls requested by Claude
    3. Return tool results back to Claude
    4. Repeat until Claude provides a final text response

    Args:
        prompt: The user's question or request
    """
    messages = [{"role": "user", "content": prompt}]
    tools = [calculate_portfolio_value_spec, calculate_spec]

    # Agent loop: continue until we get a response without tool calls
    while True:
        response = call_claude(messages, tools=tools)

        # Add Claude's response to the conversation
        messages.append({"role": "assistant", "content": response.content})

        # Check if Claude wants to use any tools
        tool_calls = [block for block in response.content if getattr(block, "type", None) == "tool_use"]

        if not tool_calls:
            # No more tool calls - extract and return the final answer
            final_answer = "\n".join([
                getattr(block, "text", "")
                for block in response.content
                if getattr(block, "type", None) == "text"
            ])

            # Parse JSON response (system prompt ensures JSON format)
            try:
                result_json = parse_json_response(final_answer)
                print(result_json.get("result"))
            except json.JSONDecodeError:
                # Fallback: print raw response if JSON parsing fails
                print(final_answer)

            return

        # Execute all tool calls and collect results
        tool_results = []
        for tool_call in tool_calls:
            try:
                result = execute_tool_call(tool_call)
                content = json.dumps(result) if isinstance(result, dict) else str(result)
            except (KeyError, ValueError, ZeroDivisionError) as e:
                content = json.dumps({"error": str(e)})

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": content,
                }
            )

        # Add all tool results to the conversation in a single user message
        messages.append({"role": "user", "content": tool_results})


# =============================================================================
# Test Prompts & Runner
# =============================================================================

# Test prompts from the assessment
prompt0 = "Use the stock tool to look up the 'tsla' ticker"
prompt1 = "What's Tesla's stock price?"
prompt2 = "Help me solve this math problem: 173 * 3232 + 342 / 72.1"
prompt3 = "Help me solve this math problem: sqrt(234.13) + ln(27389140.25) + 173 * 32 + 4.5^2."
prompt4 = "How much would it cost to buy 15 shares of tesla, 24 shares of google, and 120 shares of amazon?"
prompt5 = "Hi, what capabilities do you have?"


def run_all_tests() -> None:
    """
    Run all test prompts.
    """
    TEST_PROMPTS = [
        ("prompt0", prompt0),
        ("prompt1", prompt1),
        ("prompt2", prompt2),
        ("prompt3", prompt3),
        ("prompt4", prompt4),
        ("prompt5", prompt5),
    ]

    separator = "=" * 60

    print(f"\n{separator}")
    print("Running tests")
    print(separator)

    for name, prompt in TEST_PROMPTS:
        print(f"\n{separator}")
        print(f"{name}: {prompt}")
        print(separator)
        finance_agent(prompt)


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    run_all_tests()
