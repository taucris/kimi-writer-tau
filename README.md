# Kimi Multi-Agent Novel Writing System

An intelligent multi-agent system powered by **Moonshot AI's kimi-k2-thinking model** or **Z-ai's GLM-4.6** for autonomous novel generation with an interactive terminal interface.

## Features

### Multi-Agent Architecture

- 🎯 **Four-Phase Workflow**: Planning → Plan Critique → Writing → Write Critique
- 🧠 **Specialized Agents**: Each phase has a dedicated agent with specific expertise
- ✅ **Quality Control**: Built-in critique and revision loops for plans and chapters
- 👤 **Human-in-the-Loop**: Optional approval checkpoints at configurable points

### Interactive Terminal Interface

- 💬 **Guided Q&A**: Beautiful interactive prompts walk you through configuration
- 🎨 **Rich Formatting**: Colors, tables, panels, and progress indicators
- 📡 **Real-Time Streaming**: See agent reasoning and content as it's generated
- ⚡ **Live Updates**: Tool execution, token usage, and phase transitions displayed instantly
- ✅ **Interactive Approvals**: Review plans and chapters directly in terminal

### Smart Features

- 💾 **Context Compression**: Automatically manages token limits
- 🎨 **Writing Samples**: Optionally guide the AI's writing style with preset or custom samples
- 📝 **Custom Prompts**: Fully editable system prompts for each agent
- 🔄 **Pause/Resume**: Interrupt generation anytime with Ctrl+C, resume later
- 💾 **State Persistence**: Never lose progress - all state automatically saved
- 🤖 **Multiple AI Models**: Choose between Kimi K2 Thinking or GLM-4.6

## Installation

### Prerequisites

We recommend using [uv](https://github.com/astral-sh/uv) for fast Python package management:

```bash
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup

1. **Install dependencies:**

Using uv (recommended):

```bash
uv pip install -r requirements.txt
```

Or using pip:

```bash
pip install -r requirements.txt
```

2. **Configure your API keys:**

Create a `.env` file with your API keys:

```bash
# Copy the example file
cp env.example .env

# Edit .env and add your API key(s)
# For Kimi models:
MOONSHOT_API_KEY=your-moonshot-key-here

# For DeepInfra models (GLM-4.6):
DEEPINFRA_API_KEY=your-deepinfra-key-here
```

**Note:** You only need the API key for the model you plan to use. If you're using Kimi K2 Thinking, you only need `MOONSHOT_API_KEY`. If you're using GLM-4.6, you only need `DEEPINFRA_API_KEY`.

## Quick Start

### Interactive Mode (Recommended)

Simply run:

```bash
python -m backend.cli
```

You'll be guided through a beautiful Q&A process:

1. **Project Configuration**
   - Project name
   - Novel theme/premise
   - Genre (optional)

2. **Novel Length**
   - Short Story (3,000-10,000 words, ~1-3 chunks)
   - Novella (20,000-50,000 words, ~5-15 chunks)
   - Novel (50,000-110,000 words, ~15-30 chunks)
   - Very Long Novel (110,000-200,000 words, ~30-50 chunks)
   - Custom word count

3. **AI Model Selection**
   - Kimi K2 Thinking (Moonshot) - Most advanced, has reasoning
   - GLM-4.6 (DeepInfra) - Fast, affordable alternative

4. **Writing Style** (Optional)
   - Choose from preset writing samples
   - Or paste your own custom sample (100+ characters)

5. **Approval Checkpoints**
   - Require approval after planning phase
   - Require approval after each chapter

6. **Quality Settings**
   - Max critique iterations for plan (1-10, default: 2)
   - Max critique iterations per chapter (1-10, default: 2)

7. **Review & Confirm**
   - See a summary of your configuration
   - Confirm to start generation

### Project Management

**List all projects:**

```bash
python -m backend.cli --list
```

**Resume a project:**

```bash
python -m backend.cli --resume PROJECT_ID
```

**Get help:**

```bash
python -m backend.cli --help
```

## How It Works

### Multi-Agent Architecture

The system uses four specialized agents working in sequence:

1. **Planning Agent (Story Architect)**
   - Creates comprehensive story summary
   - Develops detailed character profiles (dramatis personae)
   - Designs three-act story structure
   - Creates chapter-by-chapter plot outline

2. **Plan Critic Agent (Story Editor)**
   - Reviews all planning materials
   - Provides structured feedback
   - Requests revisions to improve quality
   - Approves plan when ready (or auto-approves after max iterations)

3. **Writing Agent (Creative Writer)**
   - Writes chapters based on approved plan
   - Optionally follows provided writing style
   - Maintains consistency with characters and plot
   - Reviews previous chapters for continuity

4. **Write Critic Agent (Chapter Editor)**
   - Reviews each completed chapter
   - Checks for quality, consistency, pacing
   - Requests revisions if needed
   - Approves chapter or auto-approves after max iterations

### The Workflow

```
1. PLANNING Phase
   └─> Story Architect creates plan materials

2. PLAN_CRITIQUE Phase
   └─> Story Editor reviews and refines plan
   └─> [Optional approval checkpoint]

3. WRITING Phase
   └─> Creative Writer writes each chapter
   └─> [Optional approval checkpoint per chapter]

4. WRITE_CRITIQUE Phase
   └─> Chapter Editor reviews and refines chapter
   └─> Loop back to WRITING for next chapter

5. COMPLETE
   └─> All chapters written and approved
```

### Smart Features

- **Token Management**: Automatic compression at 90% of 200K token limit
- **State Persistence**: Never lose progress, resume anytime
- **Real-time Streaming**: See content and reasoning as it's generated
- **Quality Control**: Built-in critique and revision loops
- **Flexible Checkpoints**: Approve plans/chapters or run fully autonomous

## Generated Output

All files are saved in `output/{project_id}/`:

```
output/novel_20251116_225042/
├── .novel_config.json          # Project configuration
├── .novel_state.json            # Generation state (for resume)
├── summary.txt                  # Story summary
├── dramatis_personae.txt        # Character profiles
├── story_structure.txt          # Three-act structure
├── plot_outline.txt             # Chapter-by-chapter outline
├── chunk_1.txt                  # Chapter 1
├── chunk_2.txt                  # Chapter 2
├── chunk_3.txt                  # Chapter 3
└── conversation_log.json        # Full conversation history
```

**View your novel:**

- Open files in any text editor
- Use VS Code: `code output/novel_20251116_225042`
- Browse in your file explorer
- Read in terminal: `cat output/novel_20251116_225042/chunk_1.txt`

## Terminal UI Features

### Real-Time Display

**Phase Transitions:**

```
============================================================
Phase Transition: PLANNING → PLAN_CRITIQUE
============================================================
```

**Tool Execution:**

```
🔧 Tool Call: write_summary
   {'filename': 'summary.txt', ...}
   ✓ Story summary written successfully
```

**Token Usage:**

```
📊 Tokens: 45,231/200,000 (22.6%)
```

**Streaming Content:**

- Regular content displayed in white
- Reasoning content displayed in dim italic (Kimi models)
- Tool calls highlighted in yellow
- Successes in green, errors in red

### Interactive Approvals

When approval checkpoints are enabled, you'll see:

```
============================================================
⏸  Approval Required: PLAN
============================================================

━━━ Story Summary ━━━
┌─────────────────────────────────────────────────────┐
│ A detective in Victorian London investigates...    │
│ [Full summary displayed in beautiful panel]         │
└─────────────────────────────────────────────────────┘

━━━ Character Profiles ━━━
[Character profiles displayed...]

━━━ Plot Outline ━━━
[Outline displayed...]

? Do you approve? (Y/n)
```

If you reject, you can provide feedback for revision:

```
? Please provide feedback for revision:
```

The agent will revise based on your feedback!

### Keyboard Shortcuts

- **Ctrl+C**: Pause generation and save progress
- **ESC + Enter**: Finish multiline input (theme, custom sample, feedback)

## Tips for Best Results

### Project Configuration

1. **Be Specific**: Clear themes get better results
   - Good: "A detective investigating a murder in Victorian London"
   - Less good: "Write something interesting"

2. **Choose Length Wisely**:
   - Short Story (1-3 chunks) - Quick tests, complete narratives
   - Novella (5-15 chunks) - Substantial stories
   - Novel (15-30 chunks) - Full-length novels (be patient!)
   - Very Long Novel (30-50 chunks) - Epic stories (requires time)

3. **Use Writing Samples**: Provide a sample to guide the AI's style
   - Choose from built-in samples (classic authors)
   - Or paste your own (at least 100 characters)
   - Public domain works avoid copyright issues

4. **Set Approval Checkpoints**:
   - Enable plan approval to review before writing starts
   - Enable chapter approval for granular control
   - Disable both for fully autonomous operation

### Model Selection

**Kimi K2 Thinking (Moonshot)**

- Most advanced reasoning capabilities
- Shows "thinking" process
- Best quality output
- Slower and more expensive
- Requires MOONSHOT_API_KEY

**GLM-4.6 (DeepInfra)**

- Fast generation
- More affordable ($0.45/M in, $1.90/M out)
- Good quality
- No reasoning display
- Requires DEEPINFRA_API_KEY

## Project Structure

```
kimi-writer-tau/
├── backend/                    # Core system
│   ├── cli.py                 # Interactive terminal interface
│   ├── agent_loop.py          # Multi-agent orchestration
│   ├── config.py              # Configuration management
│   ├── state_manager.py       # State persistence
│   ├── system_prompts.py      # Agent system prompts
│   ├── output_handler.py      # Output abstraction
│   ├── console_output.py      # Terminal UI output
│   ├── agents/                # Four specialized agents
│   │   ├── base_agent.py
│   │   ├── planning_agent.py
│   │   ├── plan_critic_agent.py
│   │   ├── writing_agent.py
│   │   └── write_critic_agent.py
│   ├── tools/                 # 22+ phase-specific tools
│   │   ├── planning_tools.py
│   │   ├── plan_critique_tools.py
│   │   ├── writing_tools.py
│   │   └── write_critique_tools.py
│   ├── model_providers/       # AI model integrations
│   │   ├── moonshot_provider.py
│   │   └── deepinfra_provider.py
│   └── utils/
│       ├── token_counter.py
│       └── file_helpers.py
├── output/                    # Generated novels
│   └── [project_id]/
│       ├── summary.txt
│       ├── dramatis_personae.txt
│       ├── story_structure.txt
│       ├── plot_outline.txt
│       └── chunk_*.txt
├── requirements.txt           # Python dependencies
├── .env                       # API keys (create from env.example)
├── README.md                  # This file
└── LICENSE                    # MIT License
```

## Troubleshooting

### "MOONSHOT_API_KEY environment variable not set"

1. Copy `env.example` to `.env`
2. Add your API key: `MOONSHOT_API_KEY=your-key-here`
3. Get your key from <https://platform.moonshot.cn/>

### "DEEPINFRA_API_KEY environment variable not set"

1. Copy `env.example` to `.env`
2. Add your API key: `DEEPINFRA_API_KEY=your-key-here`
3. Get your key from <https://deepinfra.com/>

### "401 Unauthorized" or Authentication errors

- Verify API key in `.env` file is correct
- Ensure `.env` file is in the project root directory
- Check you're using the right API key for your selected model

### "questionary not installed" or "rich not installed"

```bash
pip install questionary rich
# or
uv pip install questionary rich
```

### Generation interrupted

```bash
# List your projects to find the project ID
python -m backend.cli --list

# Resume the project
python -m backend.cli --resume PROJECT_ID
```

### Approval checkpoint stuck

- If approval dialog doesn't appear, check that questionary is installed
- The system will auto-approve if questionary is not available

## Working in VS Code (Windows/WSL)

### Recommended Setup

1. **Install Extensions**:
   - Python (Microsoft)
   - Pylance

2. **Open Terminal in VS Code** (`Ctrl+` `)

3. **Run the CLI**:

   ```powershell
   python -m backend.cli
   ```

4. **View generated files**:
   - Use Explorer sidebar to browse `output/` folder
   - Open .txt files directly in VS Code
   - Or open entire project folder: `code output/novel_20251116_225042`

## Technical Details

### Models

- **kimi-k2-thinking**: 200K context, supports reasoning
- **GLM-4.6**: 200K context, fast and affordable

### Configuration

- **Temperature**: 1.0 (optimized for creative writing)
- **Max Tokens per Call**: 65,536 (64K)
- **Context Window**: 200,000 tokens
- **Max Iterations**: 300 (safety limit)
- **Compression Threshold**: 180,000 tokens (90% of limit)

### Dependencies

- **Python**: 3.10+
- **Core**: openai, httpx, pydantic, python-dotenv
- **Terminal UI**: questionary, rich
- **Optional backend**: fastapi, uvicorn (for future web UI)

## License

MIT License with Attribution Requirement - see [LICENSE](LICENSE) file for details.

**Commercial Use**: If you use this software in a commercial product, you must provide clear attribution to Pietro Schirano (@Doriandarko).

**API Usage**: This project uses Moonshot AI and DeepInfra APIs. Please refer to their respective terms of service for API usage guidelines.

## Credits

- **Created by**: Pietro Schirano ([@Doriandarko](https://github.com/Doriandarko))
- **Powered by**: Moonshot AI's kimi-k2-thinking model & DeepInfra's GLM-4.6
- **Terminal UI Enhancement**: Refactored for streamlined CLI-first experience

---

**Enjoy creating novels with AI!** 🚀📚
