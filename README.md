# Finance Agent Tutorial

In this guide, you'll learn best practices for tool calling by walking through the creation of a finance agent powered by Claude AI. You'll see how to implement an agentic loop that lets Claude dynamically invoke tools, run multiple actions in parallel for efficiency, and always return clean, structured JSON responses.

## Prerequisites

- Python 3.10 or higher (required for `match` statement syntax)
- An Anthropic API key

## Installation

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install anthropic python-dotenv
```

2. Get your Anthropic API key:
   - Visit [https://console.anthropic.com/](https://console.anthropic.com/)
   - Sign up or log in to your account
   - Navigate to API Keys in the dashboard
   - Generate a new API key (note: for security reasons, the key is only viewable once, so make sure to copy it immediately)
   - Copy the key (it starts with `sk-ant-`)

3. Set up your environment:
   - Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   - Open `.env` and add your API key:

   ```
   ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
   ```

   **Important**: The `.env` file is in `.gitignore` to prevent accidentally committing your API key. Never commit sensitive credentials to version control!

## Usage

Run the agent by executing the Python script:

```bash
python agent.py
```

By default, it runs `prompt0`. To test other prompts, uncomment the relevant lines at the bottom of `agent.py`.

**Example: Run a specific test prompt**

```python
finance_agent(prompt0)  # Currently active
# finance_agent(prompt1)  # Uncomment to test
# finance_agent(prompt2)
# etc.
```

## What the agent can do

The finance agent provides two main capabilities: stock price lookups and mathematical calculations.

### Stock price lookups

You can look up current prices for major stocks. The agent uses the `calculate_portfolio_value` tool with a quantity of 1 to retrieve single stock prices.

**Example: Look up Tesla's stock price**

```python
finance_agent("What's Tesla's stock price?")
# Returns: 245.60
```

Available tickers (you can add more!):

- `aapl` - Apple
- `msft` - Microsoft
- `nvda` - NVIDIA
- `goog`/`googl` - Alphabet (Google)
- `amzn` - Amazon
- `meta` - Meta (Facebook)
- `tsla` - Tesla

**How to add more tickers:**  
To support additional stocks, just add them to the `STOCK_PRICES` dictionary at the top of `agent.py` and `agent_with_tool_runner.py` in this format:
```python
"NEW_TICKER": {"price": 123.45, "name": "Company Name"},
```
Then you can immediately use the new ticker in prompts!


### Mathematical calculations

The agent performs calculations with full precision using the `calculate` tool. This ensures accurate results without relying on Claude's internal math capabilities.

**Use this when**: You need precise numerical computations, especially for complex expressions or when accuracy is critical.

**Example: Solve a multi-step math problem**

```python
finance_agent("Help me solve this math problem: 173 * 3232 + 342 / 72.1")
# Returns: 559,140.74341
```

Supported operations:
- Addition (`+`)
- Subtraction (`-`)
- Multiplication (`*`)
- Division (`/`)
- Exponentiation (`**`) - e.g., square root with `**0.5`
- Logarithm (`log`) - e.g., natural log with base e

### Combined queries

The agent can combine multiple capabilities in a single query. It breaks down complex requests into steps, using tools as needed to gather information and perform calculations.

**Use this when**: You need to combine stock price lookups with calculations, such as portfolio valuation or cost calculations.

**Example: Calculate portfolio value for multiple stocks**

```python
finance_agent("How much would it cost to buy 15 shares of tesla, 24 shares of google, and 120 shares of amazon?")
# Returns: 29,838
```

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

This approach allows Claude to handle multi-step problems that require gathering information, performing calculations, and combining results.

### Multiple tool calls (parallel execution)

The agent handles multiple tool calls in a single response. When Claude requests multiple tools simultaneously, the agent extracts all tool calls, executes them, and returns all results in a single user message. This follows the [Claude documentation on multiple tool calls](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview#multiple-tool-example) and reduces the number of API turns needed.

**Use this pattern when**: Claude identifies independent operations that can be executed together, such as multiple stock lookups or separate mathematical calculations.

The agent processes multiple tool calls as follows:

1. Extract all tool calls from Claude's response
2. Execute all tool calls (in sequence, but they're independent operations)
3. Return all results in a single user message with multiple `tool_result` blocks

**Example: Parallel calculation execution**

For the query `"173 * 3232 + 342 / 72.1"`, Claude can call both the multiplication and division tools in the same response, then add the results in a follow-up turn. This reduces the number of API calls from 3 turns to 2 turns.

## Output consistency

The agent enforces JSON-only output for structured responses. This ensures consistent parsing and integration with downstream systems.

### System prompt + temperature=0

The current implementation uses a system prompt combined with temperature=0 to enforce JSON format. This approach works well for most use cases and keeps the code maintainable.

**Use this approach when**: You need consistent JSON output without adding complexity to the agent loop, or when building demos and prototypes.

The implementation uses three mechanisms:

1. **System prompt** explicitly instructs Claude to return JSON-only format:
   ```
   CRITICAL: Your final response MUST be ONLY valid JSON with no additional text before or after
   Use this exact format: {"result": <number or string>, "explanation": "<brief optional explanation>"}
   ```

2. **Temperature=0.0** ensures deterministic, consistent output by removing randomness from Claude's responses

3. **JSON parser with fallback** handles edge cases if extra text appears, extracting JSON from the response text

This approach provides good consistency while maintaining code readability and maintainability.

### Alternative: Prefill approach

Prefilling forces Claude to start with a specific format by providing a partial assistant message. This technique is documented in [Claude's output consistency guide](https://docs.claude.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency) and provides stricter JSON enforcement than system prompts alone.

**Use this approach when**: You need absolute guarantee of JSON format, you're seeing occasional text before JSON in responses, or you're building a production system where consistency is critical.

**Example: Force JSON format with prefilling**

```python
# When you expect the final response (after tool results)
messages_with_prefill = messages + [
    {"role": "assistant", "content": '{"result":'}
]
response = call_claude(messages_with_prefill, tools=tools)

# Combine prefill with response continuation
final_answer = '{"result":' + extract_text_blocks(response)
```

**Trade-offs:**
- Adds complexity to the agent loop
- Requires tracking when to apply prefill (typically after tool results)
- For demos and most use cases, system prompt + temperature=0 is sufficient

The current implementation uses system prompt + temperature=0 for better readability and maintainability, while still providing reliable JSON output.

## Using beta tools (alternative implementation)

Anthropic provides beta features that simplify tool implementation: the `@beta_tool` decorator and `tool_runner()` method. The tool runner provides an out-of-the-box solution for executing tools with Claude, automatically handling tool execution, request/response cycles, and conversation state management.

**Use this approach when**: You want to reduce boilerplate code, prefer Pythonic tool definitions, or want Anthropic to handle the agentic loop automatically. Anthropic [recommends using the tool runner for most use cases](https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use#tool-runner-beta) as it provides type safety, validation, and automatic error handling.

### @beta_tool decorator

The `@beta_tool` decorator automatically generates tool specifications from your function signatures and docstrings. This eliminates the need to manually create JSON schema dictionaries for each tool.

**Example: Define a tool with @beta_tool**

```python
from anthropic import beta_tool

@beta_tool
def calculate_portfolio_value(stocks: list) -> str:
    """Get stock prices and calculate portfolio values.
    
    Can be used for single stock lookups (quantity=1) or multiple stocks.
    
    Args:
        stocks: List of dicts, each with 'ticker' (str) and 'quantity' (int/float).
                For single stock price: [{"ticker": "tsla", "quantity": 1}]
    
    Returns:
        A JSON string with breakdown per stock and total value
    """
    # Implementation here
    return json.dumps(result)
```

The decorator automatically:
- Extracts parameter types from function signatures
- Generates tool descriptions from docstrings
- Creates JSON schemas for tool inputs
- Handles tool result formatting

### tool_runner() method

The `client.beta.messages.tool_runner()` method automatically handles the agentic loop. You provide your tools and initial prompt, and it manages the conversation flow, tool execution, and response handling.

**Example: Use tool_runner for automatic agent loop**

```python
runner = client.beta.messages.tool_runner(
    model="claude-3-5-haiku-20241022",
    max_tokens=1024,
    temperature=0.0,
    system=SYSTEM_PROMPT,
    tools=[calculate_portfolio_value, calculate],  # Decorated functions
    messages=[{"role": "user", "content": prompt}],
)

# Iterate through messages until conversation completes
final_message = None
for message in runner:
    final_message = message

return final_message
```

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

See `agent_with_tool_runner.py` for a complete example using beta tools. The functionality is identical to `agent.py`, but with significantly less code. For more details, see the [official tool runner documentation](https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use#tool-runner-beta).

## Architecture

The agent consists of these components:

- **Tools**: `calculate_portfolio_value()` (handles single stocks with quantity=1) and `calculate()` functions
- **Tool specifications**: JSON schemas describing each tool's interface
- **Agent loop**: `finance_agent()` function managing the conversation flow
- **API helper**: `call_claude()` function wrapping the Anthropic API
- **JSON parser**: `parse_json_response()` extracts JSON from Claude's responses with fallback handling

### Architecture diagram

```mermaid
flowchart TD
    Start([User Query]) --> Agent[finance_agent]
    
    Agent --> CallAPI[call_claude]
    CallAPI --> ClaudeAPI[Claude API<br/>temperature=0.0]
    
    ClaudeAPI --> Response{Response Type?}
    
    Response -->|Tool Calls| ExtractTools[extract_tool_calls]
    Response -->|Text Only| ExtractText[extract_text_blocks]
    
    ExtractTools --> Execute[Execute All Tool Calls]
    
    Execute --> Tool1[calculate_portfolio_value<br/>Get stock prices]
    Execute --> Tool2[calculate<br/>Math operations]
    
    Tool1 --> Format1[format_tool_result]
    Tool2 --> Format2[format_tool_result]
    
    Format1 --> CollectResults[Collect All Results]
    Format2 --> CollectResults
    
    CollectResults --> AddToMessages[Add tool_results<br/>to messages]
    AddToMessages --> Agent
    
    ExtractText --> ParseJSON[parse_json_response]
    ParseJSON --> Output([Print Result])
    
    style Agent fill:#e1f5ff
    style ClaudeAPI fill:#fff4e1
    style Tool1 fill:#e8f5e9
    style Tool2 fill:#e8f5e9
    style Output fill:#f3e5f5
```

### Agent loop flow

```mermaid
sequenceDiagram
    participant User
    participant Agent as finance_agent
    participant API as Claude API
    participant Tools as Tool Functions
    
    User->>Agent: User query/prompt
    Agent->>API: Send prompt + tools
    
    loop Agent Loop
        API-->>Agent: Response (text or tool_use)
        
        alt Tool Calls Detected
            Agent->>Agent: extract_tool_calls()
            Agent->>Tools: execute_tool_call() for each
            
            par Parallel Tool Execution
                Tools-->>Agent: calculate_portfolio_value()
                Tools-->>Agent: calculate()
            end
            
            Agent->>Agent: format_tool_result()
            Agent->>API: Send tool_results back
            API-->>Agent: New response
        else No Tool Calls (Final Answer)
            Agent->>Agent: extract_text_blocks()
            Agent->>Agent: parse_json_response()
            Agent->>User: Print result
        end
    end
```

### Component architecture

```mermaid
graph TB
    subgraph "Agent Layer"
        FA[finance_agent<br/>Main Agent Loop]
        ET[extract_tool_calls<br/>Extract tool_use blocks]
        EX[extract_text_blocks<br/>Extract text blocks]
    end
    
    subgraph "API Layer"
        CC[call_claude<br/>API Wrapper]
        SP[SYSTEM_PROMPT<br/>JSON format instructions]
    end
    
    subgraph "Tool Layer"
        ETC[execute_tool_call<br/>Route to tool]
        FTR[format_tool_result<br/>Format response]
        
        CPV[calculate_portfolio_value<br/>Stock prices]
        CALC[calculate<br/>Math operations]
    end
    
    subgraph "Data Layer"
        SP_D[STOCK_PRICES<br/>Stock data]
    end
    
    subgraph "Response Processing"
        PJR[parse_json_response<br/>Extract JSON]
    end
    
    FA --> CC
    FA --> ET
    FA --> EX
    CC --> SP
    
    FA --> ETC
    ETC --> CPV
    ETC --> CALC
    CPV --> SP_D
    ETC --> FTR
    
    EX --> PJR
    PJR --> FA
    
    style FA fill:#e1f5ff
    style CC fill:#fff4e1
    style CPV fill:#e8f5e9
    style CALC fill:#e8f5e9
    style SP_D fill:#fce4ec
```

## Troubleshooting

### "Module not found" error
Make sure you've installed the Anthropic SDK:
```bash
pip install anthropic
```

### API key errors
- Verify your API key is correctly copied (should start with `sk-ant-`)
- Check that you have API credits in your Anthropic account
- Ensure there are no extra spaces or quotes around the key

### Tool execution errors

The agent includes error handling for unknown tools. If you see tool errors, check that:
- Stock tickers are lowercase
- Math operations are valid (`+`, `-`, `*`, `/`, `**`, `log`)

## Next steps

To extend the agent further, consider:

1. **Optimization**: Reduce the number of API calls by encouraging parallel tool use
2. **Error handling**: Add try-catch blocks for invalid tickers or math errors
3. **Streaming**: Add response streaming for better user experience
4. **Real-time data**: Integrate with live stock price APIs
5. **Extended math**: Support more complex operations (trig functions, etc.)

## Additional resources

To learn more about building agents with Claude and best practices for tool use:

### Agent design and best practices
- [**Effective Context Engineering for AI Agents**](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) - Learn how to structure context and prompts for reliable agent behavior
- [**Writing Tools for Agents**](https://www.anthropic.com/engineering/writing-tools-for-agents) - Best practices for designing effective tools that agents can use reliably

### Tool use documentation
- [**Implement Tool Use**](https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use) - Official Claude documentation on implementing tool use with the API

These resources provide deeper insights into:
- How to write clear tool descriptions
- Strategies for reducing API turns
- Error handling patterns
- Testing and debugging agents
- Production deployment considerations
