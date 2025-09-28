# HackUMBC 2025 – Career Path Visualizer

This is a Python prototype that generates a **career path graph** based on a user’s past courses, internships, clubs, and research, showing the steps needed to reach a target company and position. The graph is a fullscreen, left-to-right timeline with colored nodes:

- 🟩 User  
- 🟢 Completed activities  
- 🔴 Missing activities  
- 🔵 Target job  

---

## Requirements

- Python 3.10+ (tested on 3.13)
- Virtual environment recommended

Dependencies:

```bash
pip install pandas faker pyvis networkx
```
```bash
hackumbc2025/
├─ src/
│  ├─ demo_visualize.py   # Main script
│  ├─ generate_data.py    # Generates synthetic people & experience CSVs
├─ data/
│  ├─ people.csv
│  ├─ experiences.csv
├─ plan.html              # Output visualization (after running)
```


## Generate synthetic data
python3 src/generate_data.py

## Run the visualization:
```bash
python3 src/demo_visualize.py \
  --company AcmeTech \
  --position "Machine Learning Engineer" \
  --name "Alex" \
  --courses "CS101,ML201" \
  --internships "Intern - FinanceX" \
  --clubs "Robotics Club,Data Science Club" \
  --research "Research: Vision" \
  --out plan.html
```
## Open the generated html:
xdg-open plan.html

## Input Options:
```bash
--company	Target company for the career path
--position	Target job position at the company
--name	User’s name (for labeling the node)
--courses	Comma-separated list of completed courses
--internships	Comma-separated list of completed internships
--clubs	Comma-separated list of clubs
--research	Comma-separated list of research projects
--out	Output HTML filename (default: plan.html)
```
