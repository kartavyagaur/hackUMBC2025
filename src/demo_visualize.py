# src/demo_visualize.py
import pandas as pd
import networkx as nx
from pyvis.network import Network
from pathlib import Path
import argparse

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def load_data():
    people = pd.read_csv(DATA_DIR / "people.csv", dtype=str).fillna("")
    exps = pd.read_csv(DATA_DIR / "experiences.csv", dtype=str).fillna("")
    return people, exps

def aggregate_path(people, exps, target_company, target_position):
    matched_people = people[
        (people['company'].str.lower() == target_company.lower()) &
        (people['current_position'].str.lower() == target_position.lower())
    ]
    if matched_people.empty:
        # fallback to company-level
        matched_people = people[people['company'].str.lower() == target_company.lower()]

    person_ids = matched_people['person_id'].unique().tolist()
    if len(person_ids) == 0:
        return {'top_courses': pd.Series(dtype=int),
                'top_interns': pd.Series(dtype=int),
                'top_clubs': pd.Series(dtype=int),
                'top_research': pd.Series(dtype=int)}

    # filter experiences for these people
    subset = exps[exps['person_id'].isin(person_ids)]
    top_courses = subset[subset['experience_type']=='course']['title'].value_counts()
    top_interns = subset[subset['experience_type']=='internship']['title'].value_counts()
    top_clubs = subset[subset['experience_type']=='club']['title'].value_counts()
    top_research = subset[subset['experience_type']=='research']['title'].value_counts()
    return {'top_courses': top_courses, 'top_interns': top_interns, 'top_clubs': top_clubs, 'top_research': top_research, 'matched_people': matched_people}

def profile_diff(user_profile, agg, top_n=6):
    need = {'courses':[], 'internships':[], 'clubs':[], 'research':[]}
    for t, key in [(agg['top_courses'],'courses'), (agg['top_interns'],'internships'), (agg['top_clubs'],'clubs'), (agg['top_research'],'research')]:
        items = list(t.index[:top_n]) if not t.empty else []
        for it in items:
            if it not in user_profile.get(key, []):
                need[key].append(it)
    return need

def render_graph(user_profile, needs, target_company, target_position, out_html="plan.html"):
    """
    Fixed-position layout:
    - YOU at far-left, target at far-right.
    - done nodes stacked vertically around left-mid.
    - missing nodes stacked vertically around right-mid.
    - nodes have fixed x,y so the network won't auto-resize/zoom into a blob.
    """
    import math
    G = nx.DiGraph()
    user_id = f"YOU::{user_profile.get('name','You')}"
    G.add_node(user_id, title=f"User: {user_profile.get('name','You')}", group='user')

    nodes_done, nodes_missing = [], []
    for c in user_profile.get('courses', []):
        n = f"course:{c}"
        G.add_node(n, title=f"Course: {c}", group='done'); G.add_edge(user_id, n); nodes_done.append(n)
    for i in user_profile.get('internships', []):
        n = f"intern:{i}"
        G.add_node(n, title=f"Intern: {i}", group='done'); G.add_edge(user_id, n); nodes_done.append(n)
    for cl in user_profile.get('clubs', []):
        n = f"club:{cl}"
        G.add_node(n, title=f"Club: {cl}", group='done'); G.add_edge(user_id, n); nodes_done.append(n)
    for r in user_profile.get('research', []):
        n = f"research:{r}"
        G.add_node(n, title=f"Research: {r}", group='done'); G.add_edge(user_id, n); nodes_done.append(n)

    for c in needs['courses']:
        n = f"course_missing:{c}"
        G.add_node(n, title=f"Course (missing): {c}", group='missing'); G.add_edge(user_id, n); nodes_missing.append(n)
    for i in needs['internships']:
        n = f"intern_missing:{i}"
        G.add_node(n, title=f"Intern (missing): {i}", group='missing'); G.add_edge(user_id, n); nodes_missing.append(n)
    for cl in needs['clubs']:
        n = f"club_missing:{cl}"
        G.add_node(n, title=f"Club (missing): {cl}", group='missing'); G.add_edge(user_id, n); nodes_missing.append(n)
    for r in needs['research']:
        n = f"research_missing:{r}"
        G.add_node(n, title=f"Research (missing): {r}", group='missing'); G.add_edge(user_id, n); nodes_missing.append(n)

    target = f"{target_company}::{target_position}"
    G.add_node(target, title=f"Target: {target_position} @ {target_company}", group='target')
    for n in nodes_done + nodes_missing:
        G.add_edge(n, target)

    # Create pyvis net
    net = Network(
        directed=True,
        height="100vh",   # Full viewport height
        width="100%",     # Full width
        bgcolor="#ffffff",
        notebook=False
    )

    net.from_nx(G)

    # Group nodes by their assigned group so we can compute vertical stacks
    columns = {'user': [], 'done': [], 'missing': [], 'target': []}
    for node in net.nodes:
        grp = node.get('group', '')
        if grp not in columns:
            columns.setdefault(grp, []).append(node)
        else:
            columns[grp].append(node)

    # X coordinates: tune these to stretch left->right on your screen
    left_x = -2500      # YOU
    left_mid_x = -600   # done nodes (left of center)
    right_mid_x = 600   # missing nodes (right of center)
    right_x = 2500      # target

    # Vertical spacing (tweak if nodes overlap)
    vspace = 120

    # Helper to assign positions for a list of nodes
    def assign_column_positions(nodes_list, x_coord, vspacing=vspace):
        n = len(nodes_list)
        if n == 0:
            return
        # center them vertically around y=0
        start = -((n - 1) / 2.0) * vspacing
        for i, node in enumerate(nodes_list):
            y = start + i * vspacing
            node['x'] = x_coord
            node['y'] = y
            # fix both coordinates so the layout does not change
            node['fixed'] = {'x': True, 'y': True}

    # assign positions
    assign_column([n for n in net.nodes if n['group']=='user'], left_x)
    assign_column([n for n in net.nodes if n['group']=='done'], mid_left_x)
    assign_column([n for n in net.nodes if n['group']=='missing'], mid_right_x)
    assign_column([n for n in net.nodes if n['group']=='target'], right_x)

    # Style: fonts/colors/sizes
    for node in net.nodes:
        grp = node.get('group','')
        node['font'] = {"size": 20, "face": "Arial"}
        if grp == 'user':
            node['color'] = '#0B6623'  # dark green
            node['size'] = 36
        elif grp == 'done':
            node['color'] = '#2E8B57'  # sea green
            node['size'] = 26
        elif grp == 'missing':
            node['color'] = '#D32F2F'  # red
            node['size'] = 26
        elif grp == 'target':
            node['color'] = '#1565C0'  # blue
            node['size'] = 40
        else:
            node['color'] = '#9E9E9E'
            node['size'] = 20

    # Remove physics so fixed x/y are honored, and keep smooth edges off
    options = """
    {
      "nodes": {
        "font": {
          "size": 22,
          "face": "arial",
          "strokeWidth": 4,
          "strokeColor": "#ffffff"
        },
        "shape": "dot",
        "size": 30
      },
      "edges": {
        "arrows": {
          "to": { "enabled": true }
        },
        "smooth": false
      },
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "LR",
          "sortMethod": "directed",
          "levelSeparation": 350,
          "nodeSpacing": 200,
          "treeSpacing": 300
        }
      },
      "physics": {
        "enabled": false
      }
    }
    """

    net.set_options(options)

    # Write HTML
        # Write HTML (same as before)
    net.write_html(out_html, notebook=False)
    print(f"✅ Graph written to {out_html}")

    # --- Post-process HTML to hide pyvis / vis.js UI panels (toolbar, buttons, legend) ---
    # This inserts a CSS snippet into the <head> that force-hides common control-panel classes.
    # It is intentionally broad to catch different pyvis/vis.js versions.
    css_fullscreen = """
    <style>
    html, body {
        height: 100%;
        margin: 0;
        padding: 0;
        overflow: hidden;
    }
    #mynetwork {
        width: 100% !important;
        height: 100vh !important;
    }
    </style>
    """
    with open(out_html, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("</head>", css_fullscreen + "</head>")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
        # --- Inject legend at top-left ---
    legend_html = """
    <div style="
        position: fixed;
        top: 10px;
        left: 10px;
        background: rgba(255,255,255,0.9);
        padding: 10px 15px;
        border-radius: 8px;
        font-family: Arial, sans-serif;
        font-size: 16px;
        z-index: 9999;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
    ">
        <div style="margin-bottom: 4px;"><span style="display:inline-block;width:16px;height:16px;background:#0B6623;margin-right:6px;"></span>User</div>
        <div style="margin-bottom: 4px;"><span style="display:inline-block;width:16px;height:16px;background:#2E8B57;margin-right:6px;"></span>Completed</div>
        <div style="margin-bottom: 4px;"><span style="display:inline-block;width:16px;height:16px;background:#D32F2F;margin-right:6px;"></span>Missing</div>
        <div style="margin-bottom: 4px;"><span style="display:inline-block;width:16px;height:16px;background:#1565C0;margin-right:6px;"></span>Target</div>
    </div>
    """

    try:
        with open(out_html, "r", encoding="utf-8") as f:
            html = f.read()
        # Insert legend just after <body> so it overlays graph
        if "<body>" in html:
            html = html.replace("<body>", "<body>\n" + legend_html)
        else:
            html = legend_html + html
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Legend injected into graph HTML.")
    except Exception as e:
        print("⚠️ Could not inject legend:", e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", default="AcmeTech")
    parser.add_argument("--position", default="Machine Learning Engineer")
    parser.add_argument("--name", default="You")
    parser.add_argument("--courses", default="CS101,ML201")
    parser.add_argument("--internships", default="")
    parser.add_argument("--clubs", default="")
    parser.add_argument("--research", default="")
    parser.add_argument("--out", default="plan.html")
    args = parser.parse_args()

    user_profile = {
        "name": args.name,
        "courses": [c.strip() for c in args.courses.split(",") if c.strip()],
        "internships": [c.strip() for c in args.internships.split(",") if c.strip()],
        "clubs": [c.strip() for c in args.clubs.split(",") if c.strip()],
        "research": [c.strip() for c in args.research.split(",") if c.strip()]
    }

    people, exps = load_data()
    agg = aggregate_path(people, exps, args.company, args.position)
    needs = profile_diff(user_profile, agg, top_n=6)
    print("Missing summary:", needs)
    render_graph(user_profile, needs, args.company, args.position, out_html=args.out)

if __name__ == "__main__":
    main()

