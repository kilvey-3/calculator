MULTI-TASK SMART CALCULATOR
===========================

This revised version removes the Admin Dashboard completely.

MAIN IMPROVEMENTS
-----------------
1. One unlimited expression field
   - No First Number / Second Number fields.
   - Users can type long expressions such as:
     12+45*232/2+23-4

2. Smart Solve
   - After a normal calculation, the system shows a calculation breakdown.
   - This makes the calculator useful for learning, not only for getting an answer.

3. Batch Calculation
   - Multiple complete expressions can be entered at once.
   - Separate expressions with a new line or semicolon.
   - Example:
       10+5*2
       sqrt(144)
       500*20%
   - Up to 50 expressions per batch.

4. Scientific calculator functions
   - sqrt, sin, cos, tan, asin, acos, atan, log, ln
   - abs, floor, ceil, exp, factorial
   - pi and e constants
   - powers, percentages, parentheses and PEMDAS

5. Statistics
   - Enter many values separated by commas.
   - Calculates count, sum, mean, median, mode, minimum, maximum,
     range, variance and standard deviation.

6. Calculation History
   - Successful calculations are stored in SQLite.
   - History can be opened and completely cleared.
   - Clicking a history item puts its expression back into the calculator.

7. Black + Orange design
   - Black background
   - Orange calculator/function buttons
   - Dark calculator-style display

NO ADMIN DASHBOARD
------------------
The Admin Dashboard has been removed intentionally.
The system now focuses on the actual calculator, its improved features,
and user calculation history.

TECHNOLOGY
----------
Python + Flask = backend and calculation processing
HTML = interface structure
CSS = black/orange design
JavaScript = calculator interaction and API communication
SQLite = calculation history

RUN
---
1. Install Python 3.
2. Open a terminal in this project folder.
3. Run:
       pip install -r requirements.txt
4. Run:
       python app.py
5. Open:
       http://127.0.0.1:5000

DEFENSE POINT
-------------
A strong difference from ordinary calculators is the combination of:
- unlimited single-expression input,
- Smart Solve calculation breakdown,
- Batch Calculation for multiple expressions,
- scientific calculations,
- statistics,
- and persistent history with clear-history control.

The project is not claiming to be the only calculator with these features.
Its improvement is how these functions are integrated into one simple
expression-based calculator designed for the project requirements.
