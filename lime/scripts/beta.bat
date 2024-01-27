python main.py ^
    -f ../datasets/wordle-qa-2/rules-qa/input-rules-qa-1.md ^
    -m "gpt-3.5-turbo" ^
    -u 4 ^
    -v 1 

    @REM -y ^
@REM -f ../wordle-qa-1/kappa/input-common-sense-1.md ^
@REM -f ../wordle-qa-1/delta/input-noanswer.md ^
@REM -m ../../data/llama-2-7b.Q4_K_M.gguf ^
@REM -m "gpt-3.5-turbo" ^
@REM -m "llama_7b" ^
@REM -d ../wordle-qa-1/beta/ ^
@REM -m "gpt-4" ^
@REM -y

@REM -y
@REM -d ../wordle-qa-1/alpha/ ^
@REM -f ../wordle-qa-1/alpha/input-basic.md ^