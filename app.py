import streamlit as st # type: ignore
import boto3
import json
from langchain_core.prompts import PromptTemplate
import re

# Create a Bedrock Runtime client in the AWS Region of your choice.
client = boto3.client("bedrock-runtime", region_name="us-west-2")

# Set the model ID, e.g., Claude 3 Haiku.
model_id = "anthropic.claude-3-haiku-20240307-v1:0"

st.title('Intelligent Correction')
# Create prompt template
# declare variables 
grade = st.text_input('Class')
max_marks = st.text_input('Maximum marks')
partial_marks = st.toggle('Partial marks allowed')
question_type = st.selectbox('Question type', ('Short Answer','Multi Part', 'Numerical wrod problem'))
subject = st.text_input('Enter the subject')
chapter = st.text_input('Enter chapter name')
question = st.text_area('Enter the question')
accepted_answer = st.text_area('Enter accepted/best answer')
grading_criteria = st.text_area('Describe grading criteria')
student_answer = st.text_area('Enter student answer')

if partial_marks:
    partial = "Partial marks can be awarded if the answer is partially correct."
else:
    partial = "Award marks only if the answer is fully correct"
# assemble prompt
prompt = PromptTemplate.from_template("""You are a grade {grade} school teacher teaching {subject}. Your task is to evaluate a student’s answer against an accepted answer and give marks out of {max_marks} based on the optionally given grading criteria and standards.
This is a {question_type} question from the chapter {chapter}. {partial}
Question: {question}  
Accepted answer: {accepted_answer}  
Grading Criteria: {grading_criteria}
Student answer: {student_answer}

Please evaluate the student’s answer and provide most concise reason for your grading only when the student didn't score full marks. Return only marks and reason (if applicable) in XML tags and nothing else. 
- student’s marks inside <marks> </marks> tags 
- reason for your grading inside <reason> </reason> tags""")

model_prompt = prompt.invoke({"grade":grade, "subject": subject, "max_marks": max_marks, "question_type": question_type,"chapter": chapter, "partial": partial, "question": question, "accepted_answer": accepted_answer, "grading_criteria": grading_criteria, "student_answer": student_answer})

#if st.button(label = 'view prompt'):
    #st.write(f"Prompt: {model_prompt.text}")

if st.button(label = 'Evaluate student answer'):
    # Format the request payload using the model's native structure.
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": model_prompt.text}],
            }
        ],
    }
    # Convert the native request to JSON.
    request = json.dumps(native_request)

    response = client.invoke_model(modelId=model_id, body=request)

    # Decode the response body.
    model_response = json.loads(response["body"].read())

    # Extract and print the response text.
    response_text = model_response["content"][0]["text"]
    marks_response = re.search(r'<marks>(.*?)</marks>', response_text).group(1)
    st.write(f"Marks: {marks_response}")
    reason_response =re.search(r'<reason>(.*?)</reason>', response_text)
    if reason_response:
        st.write(f"Reason for grading: {reason_response.group(1)}")
    
    

