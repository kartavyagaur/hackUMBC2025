# src/generate_fake_data.py
import csv
import random
from faker import Faker
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
fake = Faker()

# small controlled vocabularies for realism
COMPANIES = ["AcmeTech","Google","Meta","StartUpX","FinanceX","BetaSoft","CrowdStrike"]
COURSES = ["CS101","DS220","ML201","ALG301","OS210","DB240","CV330"]
CLUBS = ["Robotics Club","AI Club","Security Club","Data Science Club"]
INTERNS = ["Intern - AcmeTech","Intern - Google","Intern - StartUpX","Intern - FinanceX","Research Intern - UnivX"]
RESEARCH_TOPICS = ["Vision","NLP","Robotics","Security","Recommendation"]
JOBS = ["Software Engineer","Data Scientist","Machine Learning Engineer","MLOps Engineer","Security Engineer","SRE"]

def make_people(n=120):
    people = []
    for i in range(1, n+1):
        pid = f"p{i:03d}"
        name = fake.first_name() + " " + fake.last_name()
        # sample a realistic final job and company (we will ensure some overlap)
        job = random.choices(JOBS, weights=[30,20,25,8,10,7], k=1)[0]
        company = random.choice(COMPANIES)
        people.append({"person_id": pid, "name": name, "current_position": job, "company": company})
    return people

def make_experiences(people):
    exps = []
    for p in people:
        pid = p["person_id"]
        # create a chronological list: courses -> club/research -> internship -> early job -> final job
        num_courses = random.randint(2,6)
        courses = random.sample(COURSES, k=num_courses)
        semester_base = 2018
        for idx, c in enumerate(courses):
            sem = f"Fall {semester_base + (idx // 2)}"
            exps.append({"person_id": pid, "experience_type": "course", "title": c, "organization": "University", "semester": sem})

        # maybe a club
        if random.random() < 0.7:
            club = random.choice(CLUBS)
            sem = f"Spring {semester_base + random.randint(0,4)}"
            exps.append({"person_id": pid, "experience_type": "club", "title": club, "organization": "Campus", "semester": sem})

        # maybe research
        if random.random() < 0.3:
            topic = random.choice(RESEARCH_TOPICS)
            sem = f"Summer {semester_base + random.randint(0,4)}"
            exps.append({"person_id": pid, "experience_type": "research", "title": f"Research: {topic}", "organization": "Lab", "semester": sem})

        # internships
        if random.random() < 0.85:
            intern = random.choice(INTERNS)
            sem = f"Summer {semester_base + random.randint(1,6)}"
            exps.append({"person_id": pid, "experience_type": "internship", "title": intern, "organization": intern.split(" - ")[-1], "semester": sem})

        # early job(s)
        if random.random() < 0.4:
            job = random.choice(["Junior Engineer","SWE I","Data Analyst"])
            sem = f"2019"
            exps.append({"person_id": pid, "experience_type": "job", "title": job, "organization": random.choice(COMPANIES), "semester": sem})

        # final/current job as a job experience (for tracing)
        exps.append({"person_id": pid, "experience_type": "job", "title": p["current_position"], "organization": p["company"], "semester": "2024"})
    return exps

def write_csv_people(people):
    path = DATA_DIR / "people.csv"
    with open(path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["person_id","name","current_position","company"])
        writer.writeheader()
        for r in people:
            writer.writerow(r)
    print("Wrote", path)

def write_csv_experiences(exps):
    path = DATA_DIR / "experiences.csv"
    with open(path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["person_id","experience_type","title","organization","semester"])
        writer.writeheader()
        for r in exps:
            writer.writerow(r)
    print("Wrote", path)

if __name__ == "__main__":
    people = make_people(120)
    exps = make_experiences(people)
    write_csv_people(people)
    write_csv_experiences(exps)
    print("Generated synthetic dataset in", DATA_DIR)

