import streamlit as st # type: ignore
import boto3
import json
from langchain_core.prompts import PromptTemplate
import re
import base64

with st.sidebar:
    aws_access_key_id = st.text_input("AWS Access Key Id", placeholder="access key", type="password")
    aws_secret_access_key = st.text_input("AWS Secret Access Key", placeholder="secret", type="password")

boto_session = boto3.session.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key)

# Create a Bedrock Runtime client in the AWS Region of your choice.
client = boto_session.client("bedrock-runtime", region_name="us-west-2")

st.title('Intelligent Correction')
# Create prompt template
# declare variables 
grade = st.text_input('Class')
max_marks = st.text_input('Maximum marks')
partial_marks = st.toggle('Partial marks allowed')
question_type = st.selectbox('Question type', ('Short Answer','Multi Part', 'Numerical word problem'))
subject = st.text_input('Enter the subject')
chapter = st.text_input('Enter chapter name')
question = st.text_area('Enter the question')
accepted_answer = st.text_area('Enter accepted/best answer')
grading_criteria = st.text_area('Describe grading criteria')
student_answer = st.text_area('Enter student answer or upload an image')
image_upload = st.file_uploader("Upload an image",type=['jpeg','png','jpg'])
image_uploaded = ''# empty string
# if image input:
if image_upload is not None:
    student_answer = 'Please find the students handwritten answer as image'
    image_uploaded = 'from the image of the handwritten answer '
    image_bytes = image_upload.getvalue()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

#model selction
model = st.selectbox('Choose model', ('Haiku','Sonnet','Opus'))
if model =='Haiku':
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
elif model =='Sonnet':
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
else:
    model_id = "anthropic.claude-3-opus-20240229-v1:0"

#partial marks    
if partial_marks:
    partial = "Partial marks can be awarded if the answer is partially correct."
else:
    partial = "Award marks only if the answer is fully correct"

# assemble prompt
prompt = PromptTemplate.from_template("""You are a grade {grade} school teacher teaching {subject}. Your task is to evaluate a student’s answer against an accepted answer and give marks out of {max_marks} based on the optionally given grading criteria and standards.
This is a {question_type} question from the chapter {chapter}. {partial}
<question>{question}</question> 
<acceted_answer>{accepted_answer}</acceted_answer>
<grading_criteria>{grading_criteria}</grading_criteria>
<student_answer>{student_answer}</student_answer>
Please evaluate the student’s answer {image_uploaded}and provide most concise reason for your grading only when the student didn't score full marks. Return only marks and reason (if applicable) in XML tags and nothing else. 
- student’s marks inside <marks> </marks> tags 
- reason for your grading inside <reason> </reason> tags""")

model_prompt = prompt.invoke({"grade":grade, "subject": subject, "max_marks": max_marks, "question_type": question_type,"chapter": chapter, "partial": partial, "question": question, "accepted_answer": accepted_answer, "grading_criteria": grading_criteria, "student_answer": student_answer, "image_uploaded": image_uploaded})

#if st.button(label = 'view prompt'):
    #st.write(f"Prompt: {model_prompt.text}")

if st.button(label = 'Evaluate student answer'):
    # Format the request payload using the model's native structure.
    if image_upload is not None:
        native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
        {
            "role": "user",
            "content": [
          {
            "type": "image",
            "source": {
              "type": "base64",
              "media_type": "image/jpeg",
              "data": encoded_image
            }
          },
          {
            "type": "text",
            "text": model_prompt.text
          }],}],}
    else:
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
    
    

