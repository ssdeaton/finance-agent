# Future Enhancements

## Optimization Learnings

### What Worked for Reducing Turns:
- ✅ **Combined portfolio tool** - Reduced multiple stock lookups to single call
- ✅ **Self-describing tool results** - Provided more context to the model
- ✅ **Explicit batching in system prompt** - Direct examples of batching independent operations
- ✅ **Clear "CRITICAL EFFICIENCY RULE"** - Model responds better to bold, explicit instructions

### What Didn't Work:
- ❌ **Explicit planning phase** - Added an extra turn without improving batching behavior
  - Claude can already plan internally, no need for separate planning API call
  - Better to use strong system prompt instructions instead

### Key Insight:
You can't reduce the total number of tool calls for complex math (e.g., 7 calls for "sqrt + ln + multiply + power" is minimum with binary operations), but you CAN reduce the number of turns by batching independent operations in parallel.

## Temperature Management
- [ ] Implement dynamic temperature based on conversation context
  - Use temp=0.0 for tool-calling scenarios (deterministic, accurate calculations)
  - Use temp=0.3-0.7 for conversational responses (more natural language)
  - Could detect if tools are being used in the current turn to decide
  - Makes the agent feel more natural for mixed conversation/tool-use flows

## Data Sources
- [ ] Integrate real-time stock price API (e.g., Alpha Vantage, Yahoo Finance)
  - Replace mock data with live market data
  - Add error handling for API rate limits and failures
  - Consider caching to reduce API calls
- [ ] Note: MCP (Model Context Protocol) could be useful for more complex integrations but may be overkill for deterministic data sources

## User Experience
- [ ] Evaluate streaming vs. non-streaming based on agent type
  - **Current agent**: Primarily returns numbers/short answers - streaming may not provide much value
  - **Streaming benefits**: Long-form explanations, narrative responses, step-by-step reasoning
  - **Non-streaming benefits**: Simpler implementation, better for quick factual/numerical responses
  - **Recommendation**: For calculation/lookup agents, non-streaming is often sufficient
  - If adding streaming, show tool calls in progress for better UX
- [ ] Improve error messages and user feedback
  - Better handling of invalid tickers
  - Clearer error messages for math errors (division by zero, invalid log operations)
  - Suggestions for corrections

## Functionality
- [ ] Add `evaluate_expression` tool for complex math
  - Current binary `calculate()` requires multiple chained calls for complex expressions
  - A single `evaluate_expression("sqrt(234.13) + ln(27389140.25) + 173 * 32 + 4.5^2")` could handle entire expression in one tool call
  - Would automatically handle PEMDAS/order of operations
  - Could use Python's `eval()` (with proper sandboxing) or a safe expression parser like `ast.literal_eval` with math extensions
  - Trade-off: More complex tool implementation vs. significantly fewer turns for complex math
  - This would reduce prompt3 from ~5 turns to 1 turn (call tool, get result, return answer)
- [ ] Extend math capabilities
  - Trigonometric functions (sin, cos, tan)
  - More advanced operations (factorial, modulo)
  - Support for constants (pi, e) without requiring manual input
- [ ] Add more financial tools
  - Portfolio tracking
  - Historical price data
  - Price change calculations (% gain/loss)
  - Market cap, P/E ratios, etc.

## Architecture
- [ ] Separate conversation history management
  - Store messages in a proper conversation object
  - Enable multi-turn conversations across script runs
  - Add conversation persistence
- [ ] Environment variable management
  - Move API key to environment variables
  - Add .env file support with python-dotenv
  - Create .env.example template
- [ ] Better error handling and retry logic
  - Retry on API failures
  - Exponential backoff
  - Circuit breaker pattern for tool failures

## Testing
- [ ] Add unit tests for tools
- [ ] Add integration tests for agent loop
- [ ] Test edge cases (invalid inputs, API failures, etc.)
- [ ] Performance benchmarking for turn optimization

## Documentation
- [ ] Add API reference documentation
- [ ] Create architecture diagrams
- [ ] Add more examples and use cases
- [ ] Video tutorial or demo

## Security
- [ ] Implement proper API key management (never commit keys)
- [ ] Add rate limiting
- [ ] Input validation and sanitization
- [ ] Audit logging for tool usage
