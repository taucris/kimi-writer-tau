# Quick Start Guide - Kimi Multi-Agent Novel Writing System

## For First-Time Users

### 1. Set Up Your Environment

**Create `.env` file:**
```bash
# Copy the example
cp env.example .env

# Edit .env and add your API key(s)
# For Kimi models:
MOONSHOT_API_KEY=your-moonshot-key-here

# For DeepInfra models (GLM-4.6):
DEEPINFRA_API_KEY=your-deepinfra-key-here
```

**Get API Keys:**
- Moonshot: https://platform.moonshot.cn/
- DeepInfra: https://deepinfra.com/

**Note:** You only need the API key for the model you plan to use!

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using uv (faster):
```bash
uv pip install -r requirements.txt
```

### 3. Start the Interactive CLI

Simply run:
```bash
python -m backend.cli
```

You'll see a beautiful welcome screen! 🎉

### 4. Answer the Configuration Questions

The CLI will guide you through setup:

**1. Project Information**
```
? Project name: My First Novel
? What's your novel about? (theme/premise): A detective solving a mysterious
  case in a small Victorian town
? Genre (optional): Mystery
```

**2. Novel Length**
```
? Select length:
  > Short Story (3,000-10,000 words, ~1-3 chunks)  ← Choose this for testing!
    Novella (20,000-50,000 words, ~5-15 chunks)
    Novel (50,000-110,000 words, ~15-30 chunks)
    Very Long Novel (110,000-200,000 words, ~30-50 chunks)
    Custom (specify word count)
```

**3. AI Model**
```
? Select model:
  > Kimi K2 Thinking (moonshot) - Has reasoning
    GLM-4.6 (deepinfra) - $0.45/M in, $1.90/M out - Has reasoning
```

**4. Writing Style** (Optional)
```
? Would you like to use a writing sample? No  ← You can skip this for now
```

**5. Approval Checkpoints**
```
? Require approval after planning phase? Yes  ← Recommended for first time!
? Require approval after each chunk/chapter? No
```

**6. Quality Settings**
```
? Use default settings? (2 critique iterations for plan and chunks) Yes
```

**7. Review & Confirm**
```
Configuration Summary
============================================================
  Project Name                 my_first_novel
  Theme                        A detective solving a mysterious case...
  Genre                        Mystery
  Length                       Short Story
  AI Model                     Kimi K2 Thinking
  Writing Sample               No
  Plan Approval                Yes
  Chunk Approval               No

? Proceed with generation? Yes
```

### 5. Watch the Magic Happen! ✨

You'll see real-time output as the AI works:

```
============================================================
Phase Transition: PLANNING → PLAN_CRITIQUE
============================================================

🔧 Tool Call: write_summary
   ✓ Story summary written successfully

📊 Tokens: 12,453/200,000 (6.2%)

[Agent reasoning appears in dim italic...]
[Generated content appears in white...]
```

### 6. Approve the Plan (When Asked)

When the plan is complete, you'll see:

```
============================================================
⏸  Approval Required: PLAN
============================================================

━━━ Story Summary ━━━
┌─────────────────────────────────────────────────────┐
│ [Full summary displayed...]                         │
└─────────────────────────────────────────────────────┘

━━━ Character Profiles ━━━
[Characters displayed...]

━━━ Plot Outline ━━━
[Outline displayed...]

? Do you approve? Yes
```

### 7. Novel Complete! 🎉

When finished:
```
============================================================
🎉 Novel Generation Complete!
============================================================

Generation Statistics
┌──────────────────────────┬──────────┐
│ Metric                   │ Value    │
├──────────────────────────┼──────────┤
│ Total Iterations         │ 23       │
│ Chunks Written           │ 3        │
└──────────────────────────┴──────────┘

📁 Output Directory: output/novel_20251116_225042/
```

### 8. Read Your Novel!

Your files are in the output directory:

```bash
# Browse files
ls output/novel_20251116_225042/

# Read a chapter
cat output/novel_20251116_225042/chunk_1.txt

# Open in VS Code
code output/novel_20251116_225042
```

Files generated:
- `summary.txt` - Story summary
- `dramatis_personae.txt` - Character profiles
- `story_structure.txt` - Three-act structure
- `plot_outline.txt` - Chapter outlines
- `chunk_1.txt`, `chunk_2.txt`, etc. - Your chapters!
- `conversation_log.json` - Full AI conversation

## Common First-Time Issues

### "ModuleNotFoundError: No module named 'dotenv'" or similar
```bash
pip install -r requirements.txt
```

### "MOONSHOT_API_KEY not found" or "DEEPINFRA_API_KEY not found"
1. Make sure you created `.env` file in project root
2. Add your API key: `MOONSHOT_API_KEY=your-key-here`
3. Ensure no extra spaces or quotes around the key

### "questionary not installed" or "rich not installed"
```bash
pip install questionary rich
```

### Generation interrupted by accident (Ctrl+C)
No worries! Your progress is saved. Resume with:
```bash
# List projects to find your project ID
python -m backend.cli --list

# Resume the project
python -m backend.cli --resume PROJECT_ID
```

## Useful Commands

**Start new novel:**
```bash
python -m backend.cli
```

**List all projects:**
```bash
python -m backend.cli --list
```

**Resume a project:**
```bash
python -m backend.cli --resume novel_20251116_225042
```

**Get help:**
```bash
python -m backend.cli --help
```

## Next Steps

Once you're comfortable with the basics:

- ✨ **Try different lengths**: Experiment with Novella or Novel
- 🎨 **Use writing samples**: Guide the AI's style with your favorite authors
- ✅ **Test full approval mode**: Enable chapter approval for granular control
- 🚫 **Go fully autonomous**: Disable all approvals for hands-off generation
- 🤖 **Try different models**: Compare Kimi vs GLM-4.6 output
- 📝 **Explore custom prompts**: See `CLAUDE.md` for advanced customization

## Tips for Best Results

1. **Start Small**: Use Short Story (1-3 chunks) for your first few tests
2. **Be Specific**: Detailed themes produce better results
3. **Watch Token Usage**: Green = plenty of room, Yellow = getting full, Red = near limit
4. **Enable Plan Approval**: Review the plan before writing starts (highly recommended!)
5. **Read the Logs**: `conversation_log.json` shows the full AI dialogue
6. **Experiment**: Try different genres, styles, and configurations!

## What Each Phase Does

1. **PLANNING** (Story Architect)
   - Creates story summary
   - Develops character profiles
   - Designs story structure
   - Writes chapter outlines

2. **PLAN_CRITIQUE** (Story Editor)
   - Reviews planning materials
   - Suggests improvements
   - Approves or requests revisions

3. **WRITING** (Creative Writer)
   - Writes each chapter
   - Follows the approved plan
   - Maintains consistency

4. **WRITE_CRITIQUE** (Chapter Editor)
   - Reviews each chapter
   - Checks quality and consistency
   - Approves or requests revisions

5. **COMPLETE**
   - All done! 🎉

## Keyboard Shortcuts

- **Ctrl+C**: Pause and save (can resume later)
- **ESC + Enter**: Finish multiline input (for theme, feedback, etc.)
- **Arrow Keys**: Navigate select menus
- **Enter**: Confirm selection
- **Y/N**: Quick yes/no for confirmations

## Need More Help?

- **Full Documentation**: See `README.md`
- **Developer Guide**: See `CLAUDE.md`
- **Architecture Details**: See `implementation_plan.md`
- **Terminal UI Guide**: See `TERMINAL_UI_COMPLETE.md`

## Ready to Write?

```bash
python -m backend.cli
```

Happy writing! 🚀📚
