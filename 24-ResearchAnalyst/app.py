import streamlit as st
from typing import Iterator
from agno.agent import RunResponse
from WorkflowAgent import ResearchAnalystWorkflow, ocr_pdf

# Main function
if __name__ == "__main__":
    ocr_text = ""
    user_country = ""
    pdf_path = ""
    st.title("Research Analyst Multi-Agent System")
    with st.form("input_form"):
        pdf_path = st.file_uploader("Upload a PDF file", type=["pdf"])
        user_country = st.text_input("Enter your desired research country")
        submitted = st.form_submit_button("Submit")
    if submitted and pdf_path and user_country:
        with st.spinner("Processing PDF..."):
            # save the pdf locally
            with open(f'UploadedPDF/{pdf_path.name}', "wb") as f:
                f.write(pdf_path.read())
            st.success("PDF file uploaded successfully")
            ocr_pdf(f'UploadedPDF/{pdf_path.name}')
            # read the ocr_response.md file
            with open("ocr_response.md", "r") as f:
                ocr_text = f.read()
            st.success("OCR completed successfully")
        with st.spinner("Running research workflow..."):
            # run the workflow
            workflow = ResearchAnalystWorkflow()
            # Display a placeholder for streaming
            output_placeholder = st.empty()
            full_output = ""
            # Run the workflow and stream the output
            response: Iterator[RunResponse] = workflow.run(ocr_text=ocr_text, user_country=user_country)
            for run_response in response:
                if run_response.content:
                    full_output += run_response.content
                    output_placeholder.markdown(full_output)
    else:
        st.write("No PDF file uploaded")