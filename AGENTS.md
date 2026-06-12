# Pipeline is a Python-based automation server in the style of Jenkins

## Guidlines

- Pipeline will be written in pure Python, using only the standard library.
- It will be easy to run, using only a single command.
- It will have a simple web-based user interface.
- Keep the web-based user interface clean and simple.
- It will allow people to define jobs with parameters.
- It will support local script execution for jobs, just like Jenkins.
- All configuration, for the server and jobs, will be saved as JSON files.
- Job logs will be stored on disk; there will be no SQL or similar database.
- Don't use type annotations in the Python code.
- Keep commit messages short; ideally less than 100 characters.
- When making changes to Pipeline, update its version number.
- All Python code should be formatted using black.