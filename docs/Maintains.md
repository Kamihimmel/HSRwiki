## Maintains

#### Remove Ruby tag

Using VS Code regex find & replace:

Regex prefix: `\{RUBY_B#[^\}.]*\}`
Regex suffix: `\{RUBY_E#\}`


### Generate trace data

```zsh
# update the file path to character json file
code ./scripts/update-trace-data.py

# run it
pip install -r requirement.txt
python ./scripts/update-trace-data.py
```