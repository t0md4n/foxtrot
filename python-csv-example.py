import pandas as pd
import streamlit as st

# Load CSV file
df = pd.read_csv("marketing-data.csv")

# Data cleaning: remove duplicates and handle missing values
df_cleaned = df.drop_duplicates().fillna(0)

# Quick preview
print(df.head())

st.title("Sales Dashboard")
st.write("Here's a quick look at the data:")
st.dataframe(df)