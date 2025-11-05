# Finance Agent Tutorial

The tutorial demonstrates tool calling with LLMs through a finance agent powered by Claude AI. It runs an agentic loop that lets Claude dynamically invoke tools and run multiple actions in parallel.

## Prerequisites

- Python 3.10 or higher
- An Anthropic API key, which you can get in the [Anthropic Console](https://console.anthropic.com/settings/keys).

## Installation

1. Install required dependencies:

```bash
pip install anthropic python-dotenv
```

2. Set up your environment:
   - Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   - Open `.env` and add your API key:

   ```
   ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
   ```

## Usage

Run the agent by executing the Python script:

```bash
python agent.py
```

By default, the agent runs a series of test prompts. To run an individual prompt, invoke the `finance_agent(<prompt>)` at the bottom of `agent.py`.

## What the agent can do

The finance agent provides two main capabilities: [stock price lookups](#stock-price-lookups) and [mathematical calculations](#mathematical-calculations).

### Stock price lookups

The agent uses the `calculate_portfolio_value` tool with a quantity of 1 to retrieve single stock prices, or to calculate the cost of multiple stocks. Stock prices are hardcoded, but you can extend the functionality with realtime stock APIs.

### Mathematical calculations

The agent performs calculations using the `calculate` tool. This ensures accurate results without relying on Claude's internal math capabilities.

Supported operations:
- Addition (`+`)
- Subtraction (`-`)
- Multiplication (`*`)
- Division (`/`)
- Exponentiation (`**`) - e.g., square root with `**0.5`
- Logarithm (`log`) - e.g., natural log with base e

## Example prompts

The code includes six test prompts that demonstrate various capabilities:

1. **Direct tool use**: `"Use the stock tool to look up the 'tsla' ticker"`
2. **Natural language stock query**: `"What's Tesla's stock price?"`
3. **Math calculation**: `"Help me solve this math problem: 173 * 3232 + 342 / 72.1"`
4. **Complex math with functions**: `"Help me solve this math problem: sqrt(234.13) + ln(27389140.25) + 173 * 32 + 4.5^2."`
5. **Multi-stock portfolio**: `"How much would it cost to buy 15 shares of tesla, 24 shares of google, and 120 shares of amazon?"`
6. **Capabilities inquiry**: `"Hi, what capabilities do you have?"`

## How it works

The agent uses an agentic loop pattern to handle multi-turn conversations with Claude. This pattern allows Claude to break down complex problems into steps, use tools as needed, and combine results to provide answers.

The loop follows these steps:

1. Send user prompt to Claude with available tools
2. Claude decides which tools to use (if any)
3. Execute the requested tools
4. Return results to Claude
5. Claude processes results and either:
   - Makes more tool calls (loop continues)
   - Provides final answer (loop ends)

![Finance Agent loop: Claude decides whether to respond directly or call tools (calculate_portfolio_value, calculate), executes all tool calls in parallel, and iterates until a final answer.](./agent_loop.png)

This approach allows Claude to handle multi-step problems that require gathering information, performing calculations, and combining results.

### Multiple tool calls (parallel execution)

The agent handles multiple tool calls in a single response. When Claude requests multiple tools simultaneously, the agent extracts all tool calls, executes them, and returns all results in a single user message. This follows the [Claude documentation on multiple tool calls](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview#multiple-tool-example) and reduces the number of API turns needed.

### Specific tool calling configurations

The implementation uses two specific mechanisms for accurate tool calling:

1. **System prompt** explicitly instructs Claude to return only numbers for stock or math questions:
   ```
   After using tools, provide ONLY the final answer value with no additional text, formatting, or explanation.
   - For numerical answers (stock prices, calculations): output just the number (e.g., 245.60)
   - For conversational questions: output a brief text response
   ```

2. **Temperature=0.0** ensures deterministic, consistent output by removing randomness from Claude's responses

## Optimization tutorial

The [`optimization_tutorial.ipynb` notebook](./optimization_tutorial.ipynb) demonstrates how design decisions impact API turn counts. It walks through four progressive optimizations:

1. **Baseline**: Separate tools for stock price lookup and calculation
2. **Combined portfolio tool**: Handles multiple stocks in one call
3. **Optimized system prompt**: Encourages parallel tool calls for independent operations
4. **Expression evaluator**: Safe AST-based math expression evaluation in one call

**Takeaways**:
- Combined tools significantly reduce turns for common use cases
- System prompt optimization encourages parallel execution when operations are independent
- Expression evaluators eliminate multi-step operations for math-heavy applications
- Not all queries benefit equally; focus optimization on your most frequent use cases
- Always measure turn counts to justify engineering effort

See the notebook for interactive examples, detailed comparisons, and the safe AST-based expression evaluator implementation.

### How to run the tutorial

To experiment with these optimizations yourself, follow the [prerequisites](#prerequisites) and [installation](#installation) steps for this repository.

Install the additional required [jupyter](https://pypi.org/project/jupyter/) dependency.

   ```
   pip install jupyterlab anthropic python-dotenv
   ```

Then, launch the tutorial notebook in Jupyter:
   ```
   jupyter lab optimization_tutorial.ipynb
   ```

Follow the instructions in the notebook cells. You can run each cell to observe API turn counts for various prompts and see the effect of each optimization step interactively.

If you encounter issues with missing packages or authentication, refer to the Setup section within the notebook for troubleshooting tips.

## Using beta tools (alternative implementation)

Anthropic provides beta features that simplify tool implementation: the `@beta_tool` decorator and `tool_runner()` method. The tool runner provides an out-of-the-box solution for executing tools with Claude, automatically handling tool execution, request/response cycles, and conversation state management.

The `@beta_tool` decorator automatically generates tool specifications from your function signatures and docstrings. This eliminates the need to manually create JSON schema dictionaries for each tool.

The `tool_runner()` automatically:
- Executes tools when Claude calls them
- Handles the request/response cycle
- Manages conversation state
- Provides type safety and validation
- Handles errors automatically

The tool runner returns an iterator that yields messages until the conversation completes (no more tool calls remain). This eliminates the need for manual `while` loops and message management.

### Comparing approaches

**Manual implementation (`agent.py`)**:
- Full control over agent loop logic
- Explicit tool specification dictionaries
- More code but more customization
- Better for learning how tool use works

**Beta tools (`agent_with_tool_runner.py`)**:
- Less boilerplate code
- Automatic tool specification generation
- Automatic agent loop management
- Faster to implement and maintain

**When to use each**:
- Use manual implementation when you need fine-grained control over the agent loop, want to understand the underlying mechanics, or need custom error handling beyond what the tool runner provides
- Use beta tools (tool runner) when you want to build quickly with less code, need automatic error handling, or want type safety and validation built-in

See `agent_with_tool_runner.py` for a complete example using beta tools. The functionality is the same as in `agent.py`, but with less code. For more details, see the [official tool runner documentation](https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use#tool-runner-beta).

## Next steps

To extend the agent further, consider:

1. **Structured JSON output**: Add JSON mode for downstream system integration. The current implementation uses raw text output. For production systems that need machine-parseable output, consider using Claude's response prefilling technique or the JSON schema feature to enforce structured responses. See the [output consistency documentation](https://docs.claude.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency) for implementation patterns.
2. **Optimization**: Reduce the number of API calls by encouraging parallel tool use and combining mathematical tool calls into a single expression evaluator
3. **Streaming**: Add response streaming for better user experience if designing for a conversational flow
4. **Real-time data**: Integrate with live stock price APIs
5. **Extended math**: Support more complex operations (trig functions, etc.)

## Additional resources

To learn more about building agents with Claude and best practices for tool use:

### Agent design and best practices
- [**Effective Context Engineering for AI Agents**](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) - Learn how to structure context and prompts for reliable agent behavior
- [**Writing Tools for Agents**](https://www.anthropic.com/engineering/writing-tools-for-agents) - Best practices for designing effective tools that agents can use reliably

### Tool use documentation
- [**Implement Tool Use**](https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use) - Official Claude documentation on implementing tool use with the API
