python main.py ^
    -f ../wordle-qa-1/delta/input-basic.md ^
    -m ../../data/llama-2-7b.Q4_K_M.gguf ^
    -u 4 ^
    -j ^
    -v 1 

@REM -m "gpt-3.5-turbo" ^
@REM -m "llama_7b" ^
@REM -d ../wordle-qa-1/beta/ ^
@REM -m "gpt-4" ^
@REM -y

@REM -y
@REM -d ../wordle-qa-1/alpha/ ^
@REM -f ../wordle-qa-1/alpha/input-basic.md ^