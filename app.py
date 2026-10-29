
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from ai_engine import generate_sql
from database import execute_sql

st.set_page_config(
    page_title="Smart Sales AI Assistant",
    page_icon="📊",
    layout="wide"
)

st.title("Smart Sales AI Assistant")
st.write(
    "Ask questions about your sales database in plain English. "
    "The AI generates SQL, and MySQL returns the results."
)

st.info(
    "Try: What is the total sales? "
    "Show sales by category. "
    "Which region sold the most?"
)

question = st.text_input(
    "Enter your sales question",
    placeholder="Example: Show total sales by product"
)

if st.button("Ask AI", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Generating SQL with AI..."):
                sql_query = generate_sql(question)

            st.subheader("Generated SQL")
            st.code(sql_query, language="sql")

            with st.spinner("Executing SQL in MySQL..."):
                rows = execute_sql(sql_query)

            if rows:
                df = pd.DataFrame(rows)

                st.subheader("Query Results")
                st.dataframe(df, use_container_width=True)

                # Display a chart when the results
                # contain a numeric column.
                numeric_columns = df.select_dtypes(
                    include="number"
                ).columns.tolist()

                if len(df.columns) >= 2 and numeric_columns:
                    st.subheader("Data Visualization")

                    category_columns = [
                        col for col in df.columns
                        if col not in numeric_columns
                    ]

                    if category_columns:
                        chart_df = df.set_index(
                            category_columns[0]
                        )[numeric_columns[:1]]

                        st.bar_chart(chart_df)

                st.success(
                    f"Query completed successfully. "
                    f"{len(df)} row(s) returned."
                )

            else:
                st.info("The query returned no records.")

        except Exception as error:
            st.error(f"Unable to process the question: {error}")

st.divider()
st.caption("Python | Gemini AI | MySQL | Pandas | Streamlit")
