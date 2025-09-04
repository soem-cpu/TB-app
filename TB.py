import streamlit as st
import pandas as pd
import importlib.util

st.set_page_config(page_title="Dynamic Rule-Based Data Verification", layout="wide")
st.title("📊 Dynamic Rule-Based Data Verification App")

st.markdown("""
Upload your **Python rules file** and the **Excel file** you want to verify.
The app will dynamically apply the rules and show a validation table.
""")

# Upload rules file (.py)
rules_file = st.file_uploader("Upload your Python rules file (.py)", type=["py"])
if rules_file:
    with open("rules_temp.py", "wb") as f:
        f.write(rules_file.getbuffer())

    # Load rules dynamically
    spec = importlib.util.spec_from_file_location("rules_module", "rules_temp.py")
    rules_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules_module)
    st.success("✅ Rules file loaded!")

# Upload Excel data file
data_file = st.file_uploader("Upload Excel file to verify", type=["xlsx", "csv"])
if data_file and rules_file:
    # Preview logic
    if data_file.name.endswith("xlsx"):
        xls = pd.ExcelFile(data_file)
        preview_sheet = xls.sheet_names[0]
        df_preview = xls.parse(preview_sheet)
        st.write(f"Preview of uploaded data (first sheet: {preview_sheet}):")
        st.dataframe(df_preview.head())
    else:
        df_preview = pd.read_csv(data_file)
        st.write("Preview of uploaded data:")
        st.dataframe(df_preview.head())

    # Apply rules
    try:
        # Pass file-like object to check_rules
        results = rules_module.check_rules(data_file)
        if isinstance(results, dict):
            st.markdown("## Validation Results:")
            for k, v in results.items():
                st.write(f"**{k}**")
                if isinstance(v, pd.DataFrame) and not v.empty:
                    st.dataframe(v)
                elif isinstance(v, pd.DataFrame) and v.empty:
                    st.success(f"No issues found in {k}!")
                else:
                    st.write(v)
        elif isinstance(results, pd.DataFrame):
            if results.empty:
                st.success("✅ No validation issues found!")
            else:
                st.write("Validation results:")
                st.dataframe(results)
        else:
            st.write(results)
    except Exception as e:
        st.error(f"Error running rules: {e}")

st.markdown("---")
st.markdown("Created with Streamlit")
