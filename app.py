import streamlit as st
import networkx as nx

# --- CONFIGURATION ---
st.set_page_config(page_title="Graduation Optimizer", page_icon="🎓")

# --- PART 1: THE DATA (The "IE" Input) ---
# This dictionary represents the "Precedence Constraints" (Prerequisites).
# You can edit this list to match your actual Industrial Engineering curriculum.
curriculum = {
    "Calculus 1": [],
    "Calculus 2": ["Calculus 1"],
    "Physics 1": ["Calculus 1"],
    "Differential Equations": ["Calculus 2"],
    "Linear Algebra": ["Calculus 2"],
    "Circuits": ["Physics 1", "Differential Equations"],
    "Industrial Stats": ["Calculus 2"],
    "Quality Control": ["Industrial Stats"],
    "Operations Research": ["Linear Algebra", "Industrial Stats"],
    "Simulation": ["Operations Research", "Computer Programming"],
    "Computer Programming": [], 
    "Senior Design Project": ["Simulation", "Quality Control", "Circuits"]
}

# --- PART 2: THE LOGIC (The "Engine") ---
def calculate_critical_path(passed_courses):
    # 1. Create the Network Graph
    G = nx.DiGraph()
    
    # 2. Add all connections (Prerequisites -> Course)
    for course, prereqs in curriculum.items():
        G.add_node(course)
        for p in prereqs:
            G.add_edge(p, course)

    # 3. Handle Passed Courses
    # We remove passed courses to see only the "Remaining Work"
    remaining_graph = G.copy()
    for course in passed_courses:
        if course in remaining_graph:
            remaining_graph.remove_node(course)

    # 4. Calculate Critical Path (Longest Path in DAG)
    try:
        if len(remaining_graph.nodes) == 0:
            return 0, [], remaining_graph
        
        critical_path = nx.dag_longest_path(remaining_graph)
        semesters_needed = len(critical_path)
    except nx.NetworkXError:
        # Falls here if there is a cycle (logic error in data) or empty graph
        return 0, [], remaining_graph

    return semesters_needed, critical_path, remaining_graph

# --- PART 3: THE VISUALIZATION ---
def draw_graph(G, critical_path):
    # This creates a visual flowchart using Graphviz language
    dot = nx.nx_pydot.to_pydot(G)
    
    # Style the graph
    dot.set_rankdir("LR") # Left to Right flow
    
    # Color the Critical Path nodes RED, others BLUE
    for node in G.nodes():
        n = dot.get_node(node)
        if node in critical_path:
            # Highlight Critical Path
            if isinstance(n, list): n = n[0] # Safety check
            n.set_style("filled")
            n.set_fillcolor("#ffcccc") # Light Red
            n.set_color("red")
            n.set_penwidth("2.0")
        else:
            # Standard Course
            if isinstance(n, list): n = n[0]
            n.set_style("filled")
            n.set_fillcolor("#e6f3ff") # Light Blue
            n.set_color("blue")

    return dot.to_string()

# --- PART 4: THE WEBSITE UI ---
st.title("🎓 Graduation Critical-Path Engine")
st.markdown("""
**An Industrial Engineering approach to Academic Advising.**
This tool uses *CPM (Critical Path Method)* to calculate the minimum semesters remaining based on prerequisite chains.
""")

# Sidebar
st.sidebar.header("Student Audit")
all_courses = list(curriculum.keys())
passed_selection = st.sidebar.multiselect(
    "Select courses you have PASSED:",
    options=all_courses
)

if st.button("Calculate Graduation Path"):
    semesters, path, graph = calculate_critical_path(passed_selection)

    if semesters == 0:
        st.success("🎉 You have cleared the critical path! You are ready to graduate.")
    else:
        # 1. Metric Display
        col1, col2 = st.columns(2)
        col1.metric("Min. Semesters Left", f"{semesters}")
        col1.caption("Based on prerequisite depth")
        
        col2.metric("Bottleneck Course", path[0])
        col2.caption("You must take this next!")

        # 2. The List
        st.subheader("Your Critical Path (The 'Red' Chain)")
        st.write("If you fail any course in this chain, your graduation is delayed:")
        st.error(" ➡️ ".join(path))

        # 3. The Visual Diagram
        st.subheader("Visual Network Diagram")
        st.caption("Red = Critical Path (Zero Slack) | Blue = Flexible Courses")
        
        # We need to catch error if graph is empty
        if len(graph.nodes) > 0:
            try:
                # Simple DOT graph generation manually to avoid heavy pydot dependency issues on cloud
                graph_code = 'digraph G { rankdir="LR"; node [style=filled, shape=box]; '
                for node in graph.nodes():
                    color = "lightpink" if node in path else "lightblue"
                    border = "red" if node in path else "blue"
                    graph_code += f'"{node}" [fillcolor="{color}", color="{border}"]; '
                
                for u, v in graph.edges():
                    style = "bold" if (u in path and v in path) else "solid"
                    color = "red" if (u in path and v in path) else "gray"
                    graph_code += f'"{u}" -> "{v}" [color="{color}", style="{style}"]; '
                
                graph_code += "}"
                st.graphviz_chart(graph_code)
                
            except Exception as e:
                st.warning("Could not render visual graph.")