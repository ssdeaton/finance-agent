"""
Finance Agent - Using @beta_tool and tool_runner (Beta)

This is a reimplementation of the finance agent using Anthropic's beta features:
- @beta_tool decorator for tool definitions
- client.beta.messages.tool_runner() for automatic execution

Compare this with agent.py to see how the code is different.

The @beta_tool decorator:
- Generates tool specifications from function signatures and docstrings
- Eliminates the need for manual tool spec dictionaries
- Provides cleaner, more Pythonic tool definitions

The tool_runner():
- Automatically handles the agentic loop (no manual while loop)
- Executes tools when Claude requests them
- Manages conversation flow
- Returns the final response

Documentation: https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use#tool-runner-beta
"""

import json
import math
import os
from typing import Any, Dict, List

from anthropic import Anthropic, beta_tool
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

# Centralized stock price data
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

IMPORTANT - Final Response Format:
After using tools, provide ONLY the final answer value with no additional text, formatting, or explanation.
- For numerical answers (stock prices, calculations): output just the number (e.g., 245.60)
- For conversational questions: output a brief text response
Do not include any JSON, markdown, or other formatting. Just the raw result."""


# =============================================================================
# Tool Functions with @beta_tool decorator
# =============================================================================


@beta_tool
def calculate_portfolio_value(stocks: List[Dict[str, Any]]) -> str:
    """Get stock prices and calculate portfolio values.

    Can be used for single stock lookups (quantity=1) or multiple stocks.
    Use this for ANY stock price lookup - for a single stock, use quantity=1.

    Available tickers: aapl (Apple), msft (Microsoft), nvda (NVIDIA),
    goog/googl (Google/Alphabet), amzn (Amazon), meta (Meta/Facebook),
    tsla (Tesla).

    Args:
        stocks: List of dicts, each with 'ticker' (str) and 'quantity' (int/float).
                For single stock price: [{"ticker": "tsla", "quantity": 1}]
                Example: [{"ticker": "tsla", "quantity": 15}, {"ticker": "goog", "quantity": 24}]

    Returns:
        A JSON string with breakdown per stock (including price per share) and total value

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

    result = {"breakdown": breakdown, "total_value": total_value}
    return json.dumps(result)


@beta_tool
def calculate(op: str, a: float, b: float) -> str:
    """Perform a binary mathematical operation for precise calculations.

    Args:
        op: The operation: '+' (add), '-' (subtract), '*' (multiply), '/' (divide),
            '**' (exponentiation/power), 'log' (logarithm)
        a: First number. For basic math (+, -, *, /): left operand. For '**': base.
           For 'log': the value. For sqrt, use '**' with a as the number and b as 0.5.
        b: Second number. For basic math (+, -, *, /): right operand. For '**': exponent.
           For 'log': the base (use 2.718281828459045 for natural log).

    Returns:
        A JSON string with operation details and result for better context

    Raises:
        ValueError: If operation is not supported
        ZeroDivisionError: If division by zero
        ValueError: If logarithm with invalid base
    """
    match op:
        case "+":
            calc_result = a + b
        case "-":
            calc_result = a - b
        case "*":
            calc_result = a * b
        case "/":
            if b == 0:
                raise ZeroDivisionError("Division by zero")
            calc_result = a / b
        case "**":
            calc_result = a**b
        case "log":
            if b <= 0 or b == 1 or a <= 0:
                raise ValueError(f"Invalid logarithm: log({a}, {b})")
            calc_result = math.log(a, b)
        case _:
            raise ValueError(f"Unsupported operation: {op}")

    result = {"operation": op, "a": a, "b": b, "result": calc_result}
    return json.dumps(result)


# =============================================================================
# Main Agent with @beta_tool
# =============================================================================


def finance_agent_with_runner(prompt: str):
    """
    Finance agent using Claude's @beta_tool decorator and tool_runner for automatic execution.

    Compare this with the manual agent loop in agent.py.

    The @beta_tool decorator automatically:
    - Generates tool specifications from function signatures and docstrings

    The tool_runner() automatically:
    - Handles the agentic loop (no manual while loop needed)
    - Executes tool calls when Claude requests them
    - Manages the conversation flow
    - Returns messages until no more tool calls remain

    Args:
        prompt: The user's question or request

    Returns:
        The final message from Claude
    """
    # Use client.beta.messages.tool_runner() to automatically handle tool execution
    # This returns an iterator that yields messages until the conversation is complete
    runner = client.beta.messages.tool_runner(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        tools=[calculate_portfolio_value, calculate],
        messages=[{"role": "user", "content": prompt}],
    )

    # Iterate through all messages until we get the final response
    final_message = None
    for message in runner:
        final_message = message

    return final_message


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


def run_all_tests():
    """Run all test prompts with the Tool Runner agent."""
    prompts = [
        ("prompt0", prompt0),
        ("prompt1", prompt1),
        ("prompt2", prompt2),
        ("prompt3", prompt3),
        ("prompt4", prompt4),
        ("prompt5", prompt5),
    ]

    print(f"\n{'='*60}")
    print(f"Running tests with Tool Runner")
    print(f"{'='*60}")

    for name, prompt in prompts:
        print(f"\n{'='*60}")
        print(f"{name}: {prompt}")
        print(f"{'='*60}")

        response = finance_agent_with_runner(prompt)

        # Extract and print the final answer
        # Get the last text block from the response
        text_blocks = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        final_answer = "\n".join(text_blocks)

        # Print the raw result (no JSON parsing needed)
        print(final_answer.strip())


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Finance Agent with @beta_tool and tool_runner (Beta)")
    print("=" * 60) 

    run_all_tests()
