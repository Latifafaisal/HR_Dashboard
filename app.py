import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

#config
st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")

#style
st.markdown("""
<style>
#Main background 
[data-testid="stAppViewContainer"] {
    background-color: #F7F3FA;
}
#Sidebar 
[data-testid="stSidebar"] > div:first-child {
    background-color: #5E2D91;
    color: white;
}
/* Sidebar labels and headers */
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] label {
    color: white ;
}
/* Sidebar input text */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stSelectbox div[role="button"],
[data-testid="stSidebar"] .stSlider input {
    color: black ;
}
/* Title box */
.title-box {
    background-color: #6F3AB1;
    color: white;
    padding: 25px;
    border-radius: 15px;
    text-align: center;
}
/* Section headers */
.section-header {
    background-color: #7B3FBF;
    color: white;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# DATABASE 
conn = sqlite3.connect("employees.db", check_same_thread=False)
df = pd.read_sql("SELECT * FROM employees", conn)

#  SIDEBAR FILTERS st.sidebar.header("Filters")
departments = ["All Departments"] + df['Department'].unique().tolist()
selected_dept = st.sidebar.selectbox("Department", departments, key="filter_dept")

roles = ["All Job Roles"] + df['JobRole'].unique().tolist()
selected_role = st.sidebar.selectbox("Job Role", roles, key="filter_role")

min_age, max_age = int(df['Age'].min()), int(df['Age'].max())
age_range = st.sidebar.slider("Age Range", min_value=min_age, max_value=max_age, value=(min_age, max_age), key="filter_age")

# ---------- APPLY FILTERS ----------
filtered_df = df.copy()
if selected_dept != "All Departments":
    filtered_df = filtered_df[filtered_df['Department'] == selected_dept]
if selected_role != "All Job Roles":
    filtered_df = filtered_df[filtered_df['JobRole'] == selected_role]
filtered_df = filtered_df[(filtered_df['Age'] >= age_range[0]) & (filtered_df['Age'] <= age_range[1])]

# ---------- TITLE ----------
st.markdown('<div class="title-box"><h1>HR Analytics Dashboard</h1><p>Employee Insights and Performance Management</p></div>', unsafe_allow_html=True)
st.write("")

# ---------- ANALYTICS ----------
st.markdown('<div class="section-header">Analytics</div>', unsafe_allow_html=True)

# Charts layout: two top charts side by side
top_col1, top_col2 = st.columns(2)

# 1️⃣ Average Monthly Income by Job Role
with top_col1:
    income_df = filtered_df.groupby('JobRole')['MonthlyIncome'].mean().reset_index()
    income_df.rename(columns={'MonthlyIncome':'AverageIncome'}, inplace=True)
    fig_income = px.bar(
        income_df,
        x='AverageIncome',
        y='JobRole',
        orientation='h',
        color='AverageIncome',
        color_continuous_scale=px.colors.sequential.Purples,
        text='AverageIncome',
        title='Average Monthly Income by Job Role'
    )
    fig_income.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig_income.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20),
                             yaxis=dict(title='Job Role', automargin=True),
                             xaxis=dict(title='Avg Income'))
    st.plotly_chart(fig_income, use_container_width=True)

# 2️⃣ Employee Attrition Status Pie Chart
with top_col2:
    attr_counts = filtered_df['Attrition'].value_counts().reset_index()
    attr_counts.columns = ['Attrition', 'Count']
    fig_attr = px.pie(
        attr_counts,
        values='Count',
        names='Attrition',
        color='Attrition',
        color_discrete_map={'Yes':'#D6B3FF','No':'#5E2D91'},
        title='Employee Attrition'
    )
    fig_attr.update_traces(textinfo='percent+label', textfont_size=14)
    fig_attr.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_attr, use_container_width=True)

# 3️⃣ Age Distribution Bar Chart (full width below)
st.write("")  # spacing
st.markdown("#### Age Distribution")
age_df = filtered_df['Age'].value_counts().sort_index().reset_index()
age_df.columns = ['Age', 'Count']
fig_age = px.bar(
    age_df,
    x='Age',
    y='Count',
    color='Count',
    color_continuous_scale=px.colors.sequential.Purples,
    text='Count',
    title='Employee Age Distribution'
)
fig_age.update_traces(texttemplate='%{text}', textposition='outside')
fig_age.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig_age, use_container_width=True)

# ---------- EMPLOYEE TABLE ----------
st.markdown('<div class="section-header">Employee Details</div>', unsafe_allow_html=True)
st.dataframe(filtered_df[['EmployeeNumber','Age','Department','JobRole','MonthlyIncome','PerformanceRating','Attrition']])

# ---------- MANAGEMENT ----------
st.markdown('<div class="section-header">Management</div>', unsafe_allow_html=True)

# ➕ Add New Employee
with st.expander("Add New Employee"):
    emp_number = st.number_input("Employee Number", min_value=1, value=1, key="add_emp_number")
    emp_dept = st.selectbox("Department", df['Department'].unique(), key="add_emp_dept")
    emp_role = st.selectbox("Job Role", df['JobRole'].unique(), key="add_emp_role")
    emp_age = st.number_input("Age", min_value=18, max_value=65, value=25, key="add_emp_age")
    emp_income = st.number_input("Monthly Income", min_value=1000, max_value=50000, value=5000, key="add_emp_income")
    emp_perf = st.selectbox("Performance Rating", [1,2,3,4], key="add_emp_perf")
    emp_attr = st.selectbox("Attrition", ["Yes","No"], key="add_emp_attr")
    
    if st.button("Add Employee", key="add_emp_button"):
        # Check if EmployeeNumber already exists
        existing = pd.read_sql(f"SELECT * FROM employees WHERE EmployeeNumber={emp_number}", conn)
        if not existing.empty:
            st.error(f"Employee Number {emp_number} already exists. Please use a unique number.")
        else:
            conn.execute(
                "INSERT INTO employees (EmployeeNumber, Age, Department, JobRole, MonthlyIncome, PerformanceRating, Attrition) VALUES (?,?,?,?,?,?,?)",
                (emp_number, emp_age, emp_dept, emp_role, emp_income, emp_perf, emp_attr)
            )
            conn.commit()
            st.success("Employee added successfully!")

        # Removed st.experimental_rerun()

# 💰 Update Employee Income
with st.expander("Update Employee Income"):
    emp_id = st.number_input("Employee Number", min_value=1, value=1, key="update_emp_number")
    new_income = st.number_input("New Monthly Income", min_value=1000, max_value=50000, value=5000, key="update_emp_income")
    if st.button("Update Income", key="update_income_button"):
        conn.execute("UPDATE employees SET MonthlyIncome=? WHERE EmployeeNumber=?", (new_income, emp_id))
        conn.commit()
        st.success("Income updated successfully!")
        # Removed st.experimental_rerun()
