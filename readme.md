# LIME - Micro-framework for Evals

A homebrewed Language Model Eval tool.  Specifically a cli pipeline to:
1. Parse question/answer datasets in markdown format:
1. Evaluate the language models on these datasets:
    - Inference Services:
      - OpenAI API 
      - Locally running LlamaCpp models
      - Custom PipeLine (CPL) apps
    - Grade or re-grade the completions
1. Aggregate / Summarize / Compare the results.
 

**Gallery of QA Repositories:**
- [**Hello QA**](https://github.com/sutt/hello-qa) which has different experiments around using lime to demonstrate useful functionality and patterns.
- [**Wordle dataset**](https://github.com/sutt/wordle-qa-2) which uses different multiple-choice questions about rules/strategy/reasoning for the game.


TODO - insert a diagram

### Value Proposition

TODO - insert the value prop around the complexity-spectrum of how evals are performed.

### Invoking Sub Commands

Lime is a command line tool, with three main sub-commands: `eval`, `agg`, and `grade`. Each of these sub-commands has its own set of arguments and options. To see the full list of options for each sub-command, run `lime <sub-command> --help`.

There are three main actions that can be taken with this tool:

 - `lime eval`: run a specified model on a sheet or directory of sheets, create output(s).
 - `lime agg`: aggregate and compare the results of model run(s).
 - `lime grade`: update the grading and/or ground_truth of a sheet.

In addition there are supplementary commands:

  - `lime init`: create a template config or an example dataset.
  - `lime check`: print info on version, parameters, configs, secrets, etc.

##### Run Models on Question Sheets - `lime eval <input> [args]`:
```
lime eval
  [<input>]             # input-sheet or globs
  [ -m <model_name>]    # model name
  [ -v <verbose_int>]   # verbose level, can use -v / -vv style, default 0
  [ -y / --dry_run  ]   # dry run, don't write output
  [ --debug]            # if set, print full stack trace on exception
```

Run a specified model on a specified sheet (or directory of sheets) and create an output file in the directory of the input sheet. If a directory is specified as an input one, outputs file per input-sheet) and applies grading after processing the models.

##### Aggregate and Compare Model Runs - `lime agg <input_dir> [args]`:

```
lime agg
  <input_glob>            # glob pattern for input json files
  [-v <verbose_int>]      # verbose level (prints extra info to stderr)
  [--md]                  # output optimized for disply in file
  [--terminal]            # output optimized for disply in terminal
  [--no-format]           # no justification or formatting applied to tables
  [--completions]         # table of formatted completions
  [--discrepancies]       # rows that have diff in grading
  [--discrepancies-full]  # rows that have diff in grading with respective completions
```

**Basic:** Generated summary tables of aggregation and comparison for all all output-*.json files found in the supplied input directory. Outputs this data as markdown format (from pandas) to stdout. Redirect stdout to a file to save the output, e.g. `lime agg ./data/outputs/ > ./data/outputs/agg-1.md`. 

**Formatting / Style:** Should auto-detect if the output is going to a terminal or a file and format appropriately, but you can also manually specify this with the `--md` or `--terminal` flags. When piping into `less` use the `--terminal` flag to get the best formatting. Add the `--no-format` flag to always get the full output without formatting.

**Filtering with Globs:** We can use globs to filter the input files, e.g. `lime agg ./aggfiles/*gpt-3.5*` to aggregate all output files that inclue this string in the word.

**Report Types:** By default, the output is a summary of the model runs, but you can also specify to output the `--completions`, `--discrepancies`, or `--discrepancies-full` reports as args here.


##### Grade (or re-grade) the output of a model run - `lime grade <output> [args]`:

```
lime grade
  <output>              # output json file to grade
  [-i <input_file.md>]  # input file to pull [updated] ground-truth from
  [-w ]                 # write changes; leave off for dry run
  [-v ]                 # verbose boolean
  [-l ]                 # "liberal grading" option
```

Take as required input a path to an output json file for update the grading field of each question there in. 

Optionaly, if specified with an input file to an input-sheet (`-i`) can update the ground_truth field of questions, when ground_truth is initially ill-specifed or needs to be updated.

By default this is a dry run, use the `-w` flag to write the changes to the output file.

##### Init Config or sample Dataset - `lime init <init_type> [args]`:

```
lime init
  <init_type>           # `config` or `dataset` or `sheet`
  [ --simple]           # create `simple` dataset
  [ --usr ]             # create config in home directory
  [ --inert ]           # for config, comments: present | settings: commented
  [ --full ]            # for config, comments: present | settings: active
  [ --bare ]            # for config, comments: no      | settings: active
  [ --blank ]           # for config, comments: no      | settings: no

```

Will add files of a template:
 - **`config`:** as `.lime/config.yaml` to current working directory, unless specified with `--usr` flag in which case writes to the home directory along with `secrets.env` file for holding api keys.
 - **`dataset`:** several files representing input sheets which can be used to test the tool. Currently the only option is `--simple` of two sheets with two questions.

##### Check Versions, Config, etc - `lime check [args]`:

```
lime check
  [ --dataset ]   # NotImplented - should check which datasets are available.
```

Collect and print information about current versions, config, secrets, etc. Useful for seeing if tool is configured appropriately:
 - Current working directory loads what settings via workspace config file.
 - Which local models, and api's are available.

### Quickstart

Setup up the package:
```bash
git clone https://github.com/sutt/lime
cd lime
pip install -e .
```

### Hello World

Head into a clean directory, outside of lime, and run the following:

```bash
lime init dataset --simple
set OPENAI_API_KEY=sk-...
lime eval . -v
lime agg .
```

### Further

```bash
lime grade output-common-sense-1-gpt-3.5-turbo-aaff.json -l
lime grade output-common-sense-1-gpt-3.5-turbo-aaff.json -l -w

lime grade output-common-sense-2-gpt-3.5-turbo-aaff.json -i input-common-sense-2.md
lime grade output-common-sense-2-gpt-3.5-turbo-aaff.json -i input-common-sense-2.md -w

lime agg . > agg1.md
```

```bash
lime check
lime init config --workspace
# edit the .lime/config.yaml file

```

Obviously, with the long constructed filename, tab completion in the terminal is vital to usability. To avoid low number of completions several best practices are used:
- Keep the number of input files in the directory low.
- Periodically move output files into a cetralized repo, e.g. an `./aggfiles/` directory. This allows you to run `agg` commands on all the most recent test runs, but not pollute your experiments reporting with older irrelevant data.
  - To build queries out of the `aggfiles` directory, use the globs, e.g. `lime agg ./aggfiles/*gpt-3.5*` to aggregate all output files that inclue this string in the word.

### Running Tests

```bash
# install the pytest if not installed, can be installed with
pip install lime[dev]

# from root directory...
# run default tests
pytest -vv tests/
# without specifying tests/ directory, you won't pickup the pytest.ini
# and thus won't get the `slow` tag register to preclude these tests from default

# run slow tests - these are where local llm models are run
pytest -vv -m slow tests/
```

### Custom PipeLine - CPL Apps

TODO - add more info on Custom PipeLine

### Outputs

Sample outputs of the program:

#### Output of main program run:

```json
{
  "sheet": {
    "type": "sheet",
    "name": "Rule-QA-1",
    "sub_sections": [
      {
        "type": "question",
        "name": "question",
        "text": "Below is a question about the game Wordle. Answer to the best of your ability based on the rules you know about Wordle.\n<EVAL-ENDCHAR>\n\n"
      },
      {
        "type": "meta",
        "name": "meta",
        "text": "- answer_type: mutliple-choice\n- answer suggested length: 10\n\n",
        "data": {
          "answer_type": "mutliple-choice",
          "answer_suggested_length": "10"
        }
      }
    ],
    "run_id": "2047",
    "model_name": "gpt-3.5-turbo",
    "meta_data": {
      "answer_type": "mutliple-choice",
      "answer_suggested_length": "10"
    },
    "question": "Below is a question about the game Wordle. Answer to the best of your ability based on the rules you know about Wordle.\n<EVAL-ENDCHAR>\n\n"
  },
  "questions": [
    {
      "name": "Num-Guesses-1",
      "meta_data": {
        "answer_type": "mutliple-choice",
        "answer_suggested_length": "10"
      },
      "ground_truth": "B) 6",
      "question": "Below is a question about the game Wordle. Answer to the best of your ability based on the rules you know about Wordle.\nQ: What is the maximum number of guesses you can make in a game of Wordle?\nA) 5\nB) 6\nC) 7\nD) No limit\n<EVAL-ENDCHAR1>\n\n",
      "completion": "A) 5",
      "error": null,
      "model_name": "gpt-3.5-turbo",
      "eval_time": 1.4130847454071045,
      "grade": false
    },
    {
      "name": "Num-Letter-1",
      "meta_data": {
        "answer_type": "mutliple-choice",
        "answer_suggested_length": "10"
 
```

#### Aggregate Output

##### Leaderboard: `{input_sheet, model}` on `pct_correct`

| input_name             | model_name     |   num_questions |   pct_correct |
|:-----------------------|:---------------|----------------:|--------------:|
| What Shows Up          | gpt-4          |               1 |          1    |
| What Shows Up          | gpt-3.5-turbo  |               1 |          0    |
| Simulated-Missing-1    | gpt-4          |              10 |          0.5  |
| Simulated-Missing-1    | gpt-3.5-turbo  |              20 |          0.3  |
| Simulated-Missing-1    | llama_13b_chat |              10 |          0.1  |
| Rule-QA-1              | gpt-4          |               8 |          1    |
| Rule-QA-1              | gpt-3.5-turbo  |              16 |          0.38 |
| Rule-QA-1              | llama_13b_chat |               8 |          0.38 |
| JSON-state-reasoning-1 | gpt-4          |              10 |          0.7  |
| JSON-state-reasoning-1 | gpt-3.5-turbo  |              19 |          0.53 |
| JSON-state-reasoning-1 | llama_13b_chat |               9 |          0.11 |

##### Runs: `{input_sheet, model}` on number of `run_id`'s

| input_name             | model_name     |   run_id |
|:-----------------------|:---------------|---------:|
| JSON-state-reasoning-1 | gpt-3.5-turbo  |        2 |
| Rule-QA-1              | gpt-3.5-turbo  |        2 |
| Simulated-Missing-1    | gpt-3.5-turbo  |        2 |
| JSON-state-reasoning-1 | gpt-4          |        1 |
| JSON-state-reasoning-1 | llama_13b_chat |        1 |
| Rule-QA-1              | gpt-4          |        1 |
| Rule-QA-1              | llama_13b_chat |        1 |
| Simulated-Missing-1    | gpt-4          |        1 |
| Simulated-Missing-1    | llama_13b_chat |        1 |
| What Shows Up          | gpt-3.5-turbo  |        1 |
| What Shows Up          | gpt-4          |        1 |

##### All Questions: list of all question names by sheet

| input_name             | name                        |
|:-----------------------|:----------------------------|
| JSON-state-reasoning-1 | Reason-Current-Turn-Num     |
| JSON-state-reasoning-1 | Reason-Letters-Guessed      |
| JSON-state-reasoning-1 | Reason-Letters-Guessed-2    |
| JSON-state-reasoning-1 | Reason-Win                  |
| JSON-state-reasoning-1 | Reason-Win-2                |
| JSON-state-reasoning-1 | Reason-Win-3                |
| JSON-state-reasoning-1 | Reason-Words-Guessed        |
| JSON-state-reasoning-1 | Reason-Words-Guessed-2      |
| Rule-QA-1              | Mechanics-Basic-Reasoning-1 |
| Rule-QA-1              | Mechanics-Basic-Reasoning-2 |
| Rule-QA-1              | Mechanics-Guess-Valid-Word  |
| Rule-QA-1              | Mechanics-Multiletter-1     |
| Rule-QA-1              | Num-Guesses-1               |
| Rule-QA-1              | Num-Letter-1                |
| Rule-QA-1              | Terminology-Absent-1        |
| Rule-QA-1              | Terminology-Present-1       |
| Simulated-Missing-1    | Simulated-Missing-0         |
| Simulated-Missing-1    | Simulated-Missing-1         |
| Simulated-Missing-1    | Simulated-Missing-2         |
| Simulated-Missing-1    | Simulated-Missing-3         |
| Simulated-Missing-1    | Simulated-Missing-4         |
| Simulated-Missing-1    | Simulated-Missing-5         |
| Simulated-Missing-1    | Simulated-Missing-6         |
| Simulated-Missing-1    | Simulated-Missing-7         |
| Simulated-Missing-1    | Simulated-Missing-8         |
| Simulated-Missing-1    | Simulated-Missing-9         |
| What Shows Up          | Q-1                         |



### Quicklaunch

Install the package dependencies:

```bash
pip install -r requirements.txt
```

Add your OpenAI API key to your environment variables:

```bash
OPENAI_API_KEY=sk-...
```

Get an eval dataset to run at it and run the scripts outlined above.


### Markdown Question Sheets

These are the core data structure that this tool is built around.

##### Why Markdown?
This uses markdowns as compromise between the ease of editing and the flexibility of json/yaml. Tradeoffs we're looking to hit:
- accessible to no-code users
- ease of version control diffing + cli tools (no html, no database, but not json)
- good enough control over formatting, whitespace, unicode, etc
- allows semi-structured format

##### Parsing Scheme
Parsing is dictated by a schema file, which is a yaml file that specifies the markdown headers to look for and how to parse them. `./data/md-schema.yaml` and you can specify your own schema file with the `-s` flag on the main script.

The Question Sheet iself, convention is named `input-name-version-.md` with the `input-` prefix being important to pick it when parsing a directory. It's broken into two sections: `sheet` and `question`. There is one `sheet` section is for the top-level sheet metadata and system prompt which then cascades onto the individual level  `question` objects. `meta` data is key value pairs about the question, e.g. us it multiple choice question? what is the suggested max_tokens the answer? etc.

```yaml
sheet: 
  md_header: 1
  children:
    md_header: 4
    options:
    - meta
    - question
question: 
  md_header: 2
  children:
    md_header: 4
    options:
    - meta
    - answer
    - question
```

##### End Character Token - `<EVAL-ENDCHAR\>` or `|EVAL-ENDCHAR|`

Use these to signal the end of an *question* or *answer* section and trim trailing spcae (or deliberatly allow line breaks). Since the text field will add on `\n` characters until the next markdown section is found by default. 

##### Example

In this example: 
 - the `sheet` level has:
   - `info`: for a scratchpad notes/comments.
   - `meta`: specifying key value pairs about the all the questions on this sheet.
   - `question`: for the system prompt.
 - the `question` level has multiple objects with:
   - `meta`: nothing specified here, since it cascades from sheet level
   - `answer`: for the answer to the question (using `<EVAL-ENDCHAR>`)
   - `question`: for the question text.


```markdown

# JSON-state-reasoning-1
#### info
Written 11.26.23
Revised 12.17.23

Goal: Use programming style representations of the game state to answer questions about the game.

#### meta
- answer_type: mutliple-choice
- answer suggested length: 10

#### question
Below is the state of a wordle game. Use the output of state information to answer the question.

A B O U T
S A L E S
F L A M E
□ □ □ □ □
□ □ □ □ □
□ □ □ □ □

```json
[
   [['absent', 'a'], ['present', 'b'], ['correct', 'o'], ['absent', 'u'], ['absent', 't']], 
   [['present', 's'], ['absent', 'a'], ['absent', 'l'], ['absent', 'e'], ['correct', 's']], 
   [['absent', 'f'], ['absent', 'l'], ['absent', 'a'], ['absent', 'm'], ['absent', 'e']], 
   [['empty', ''], ['empty', ''], ['empty', ''], ['empty', ''], ['empty', '']], 
   [['empty', ''], ['empty', ''], ['empty', ''], ['empty', ''], ['empty', '']], 
   [['empty', ''], ['empty', ''], ['empty', ''], ['empty', ''], ['empty', '']]
]
```
<EVAL-ENDCHAR>

## Reason-Win
#### meta
#### answer
B) No<EVAL-ENDCHAR>
#### question
Based on the output, has the player won yet?
A) Yes
B) No
<EVAL-ENDCHAR>

## Reason-Win-2
#### meta
#### answer
B) No<EVAL-ENDCHAR>
#### question
Based on the output, do we know the secret word?
A) Yes
B) No
<EVAL-ENDCHAR>

(...continued)
```
