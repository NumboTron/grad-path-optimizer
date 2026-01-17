import streamlit as st
import networkx as nx

st.set_page_config(page_title="INE Course Map", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
    }

    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stMetric, .stMarkdown, .stInfo, .stSuccess, .stError, .stWarning {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.9);
    }
</style>
""", unsafe_allow_html=True)

# --- PART 1: THE DATA (Extracted from your PDF) ---
# I have mapped the prerequisites based on standard flows and the PDF arrows.
curriculum = {
    # --- Year 1 ---
    "NGN 110 - Intro to Engineering": [],
    "CHM 101 - Chemistry": [],
    "MTH 103 - Calculus I": [],
    "PHY 101 - Physics I": ["MTH 103 - Calculus I"],
    "WRI 101 - Academic Writing I": [],
    
    "CMP 120 - Programming": [],
    "MTH 104 - Calculus II": ["MTH 103 - Calculus I"],
    "PHY 102 - Physics II": ["PHY 101 - Physics I"],
    "WRI 102 - Academic Writing II": ["WRI 101 - Academic Writing I"],

    # --- Year 2 ---
    "MTH 203 - Calculus III": ["MTH 104 - Calculus II"],
    "MTH 225 - Diff Eq & Linear Alg": ["MTH 104 - Calculus II"],
    "NGN 112 - AI & Data Science": ["CMP 120 - Programming"],
    "MCE 230 - Materials Science": ["CHM 101 - Chemistry"],
    
    "NGN 211 - Eng Probability & Stats": ["MTH 104 - Calculus II"],
    "INE 222 - Operations Research I": ["MTH 225 - Diff Eq & Linear Alg"],
    "INE 202 - Fund of Ind Eng": ["NGN 110 - Intro to Engineering"],

    # --- Year 3 ---
    "INE 322 - Operations Research II": ["INE 222 - Operations Research I"],
    "INE 323 - Stochastic Processes": ["NGN 211 - Eng Probability & Stats"],
    "INE 311 - Quality Engineering": ["NGN 211 - Eng Probability & Stats"],
    "INE 310 - Data Mgmt for IE": ["CMP 120 - Programming"],
    
    "INE 331 - Analysis of Prod Systems": ["INE 222 - Operations Research I"],
    "INE 332 - Supply Chain Analysis": ["INE 331 - Analysis of Prod Systems"],
    "INE 302 - Mfg Processes": ["MCE 230 - Materials Science"],

    # --- Year 4 ---
    "INE 418 - Decision Science": ["INE 222 - Operations Research I"],
    "INE 439 - Fundamentals of Mfg": ["INE 302 - Mfg Processes"],
    "INE 465 - Service Systems": ["INE 323 - Stochastic Processes"],
    "INE 490 - Senior Design I": ["INE 331 - Analysis of Prod Systems", "INE 311 - Quality Engineering"],
    "INE 491 - Senior Design II": ["INE 490 - Senior Design I"]
}

# --- PART 2: THE LOGIC (Critical Path Engine) ---
def calculate_critical_path(passed_courses):
    G = nx.DiGraph()
    for course, prereqs in curriculum.items():
        G.add_node(course)
        for p in prereqs:
            G.add_edge(p, course)

    remaining_graph = G.copy()
    for course in passed_courses:
        if course in remaining_graph:
            remaining_graph.remove_node(course)

    try:
        if len(remaining_graph.nodes) == 0:
            return 0, [], remaining_graph
        critical_path = nx.dag_longest_path(remaining_graph)
        semesters_needed = len(critical_path)
    except nx.NetworkXError:
        return 0, [], remaining_graph

    return semesters_needed, critical_path, remaining_graph

# --- PART 3: THE UI ---
st.title("🎓 INE Flow Optimizer")
st.markdown("**Welcome to your chill academic advisor.** Select what you've done, and we'll calculate your path.")

# Sidebar
st.sidebar.header("Your Transcript")
all_courses = list(curriculum.keys())
passed_selection = st.sidebar.multiselect("Select courses you passed:", options=all_courses)

if st.button("Calculate Path", type="primary"):
    semesters, path, graph = calculate_critical_path(passed_selection)

    if semesters == 0:
        st.balloons()
        st.success("You are free! Graduation is here.")
    else:
        # Dashboard Layout
        c1, c2, c3 = st.columns(3)
        c1.metric("Semesters Left (Min)", semesters)
        c2.metric("Remaining Courses", len(graph.nodes))
        c3.metric("Critical Bottleneck", path[0].split("-")[0]) # Shows just code (e.g., INE 331)

        st.markdown("### 🚦 The Critical Path")
        st.caption("You cannot drop these courses without delaying graduation.")
        
        # Display list nicely
        for i, course in enumerate(path):
            st.info(f"**Step {i+1}:** {course}")

        # Visualization
        st.markdown("### 🕸️ Visual Map")
        try:
            # Customizing the graph look to match the "Chill" theme
            dot_code = 'digraph G { rankdir="LR"; bgcolor="transparent"; node [style="filled", shape="box", fontname="Quicksand", penwidth="0"]; edge [penwidth="2"]; '
            
            for node in graph.nodes():
                # Critical Path = Soft Red/Pink, Others = Soft Blue/White
                if node in path:
                    color = "#ffadad" # Pastel Red
                    font = "black"
                else:
                    color = "#e0f7fa" # Pastel Blue
                    font = "#555"
                
                # Cleanup names for the graph (too long names break the visual)
                short_name = node.split("-")[0] 
                dot_code += f'"{node}" [label="{short_name}", fillcolor="{color}", fontcolor="{font}"]; '
            
            for u, v in graph.edges():
                if u in path and v in path:
                    color = "#ff6b6b" # Darker red for critical arrows
                else:
                    color = "#b0bec5" # Grey for others
                dot_code += f'"{u}" -> "{v}" [color="{color}"]; '
            
            dot_code += "}"
            st.graphviz_chart(dot_code)
            
        except Exception:
            st.warning("Visual map requires data.")

