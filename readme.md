# LIME - Eval-Pipeline

A homebrewed Language Model Eval tool.  Specifically a cli pipeline to:
 - Parse question/answer datasets in markdown format:
 - Evaluate the language models on these datasets:
    - process these datasets into openai api and locally deployed llamas models
    - automatically grade the results
 - Aggregate / summarize / compare the results.

This was built on a [Wordle dataset](https://github.com/sutt/wordle-qa-2) which uses different multiple-choice questions about rules/strategy/reasoning for the game (e.g. JSON representation).

TODO - insert a diagram

### Script Tools

There are three main actions that can be taken with this tool:

 - `main.py`: run a specified model on a sheet, create an output
 - `grader.py`: update the grading and ground_truth of a sheet
 - `agg.py`: aggregate and compare the results of multiple model runs

Run the bash scripts in the `scripts/` directory from repo root (and supplementary windows batch files) as they require multiple arguments with path and filename specification.

##### Run Models on Question Sheets - `./scripts/main.sh`:
```bash
python main.py \
   -f ../wordle-qa-2/what-shows-up/input-wsu-1.md \  #input-sheet
   # -d ../wordle-qa-2/what-shows-up \  # input-directory
   -m gpt-4 \   # model name
   -u 4 \  # number of uuid chars to generate
   -j \    # json output
   -v \  # verbose 
```
Run a specified model on a specified sheet (or directory of sheets) and create an output file in the directory of the input sheet. If a directory is specified as an input one, outputs file per input-sheet) and applies grading after processing the models.

Can use `collect_results.sh` script here to move all output files into a single directory for aggregation.

```bash
destination_dir="_results"
mkdir -p "$destination_dir"
find . -type f -name "output*" -exec mv {} "$destination_dir" \;
find . -type f -name "grade*" -exec mv {} "$destination_dir" \;

```

##### (Re)grade the output of a model run - `./scripts/grader.sh`:
```bash
python grader.py \
   -o ../wordle-qa-2/results/output-wsu-1-gpt-3.5-turbo-4bd8.json \ # output file to grade/overwrite
   -i ../wordle-qa-2/what-shows-up/input-wsu-1.md \  # optional input file
   -v \   # verbose
   -w \   # write changes; leave off for dry run
   -l \   # "liberal grading" option
```

Take as input (`-o`) an output file for update the grading field of each question there in. Optionaly, if specified with an input file to an input-sheet (`-i`) can update the ground_truth field of questions, when ground_truth is initially ill-specifed or needs to be updated.

##### Aggregate and Compare Model Runs - `./scripts/agg.sh`:

```bash
python agg.py \
   -i ../wordle-qa-2/results \
   -v 
#  -o ../wordle-qa-2/results/agg-mysummary-1.md
```

Generated summary tables of aggregation and comparison for all all output-*.json files found in the supplied input directory. Outputs this data as markdown format (from pandas) into an `agg-xxxx.md` file in the input directory (4 char uuid by default unless output filepath `-o` flag is specified).


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
