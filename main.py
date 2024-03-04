import openai
import os
from dotenv import find_dotenv, load_dotenv
import time
import logging
import re
from datetime import datetime
import requests
import json
import streamlit as st
from streamlit_lottie import st_lottie_spinner, st_lottie
from PIL import Image


load_dotenv()
client = openai.OpenAI()
model = "gpt-4-turbo-preview"



phases = [
    {
        "id": "name",
        "question": """What is your name?""",
        "sample_answer": "",
        "instructions": """The user will give you their name. Then, welcome the user to the exercise, and explain that you'll help them and provide feedback as they go. End your statement with "I will now give you your first question about the article." """,
        "rubric": """
            1. Name
                    1 point - The user has provided a response in this thread. 
                    0 points - The user has not provided a response. 
        """,
        "label": "GO!",
        "minimum_score": 0
    },
    {
        "id": "about",
        "question": """What is the article about?""",
        "sample_answer":"This article investigates the impact of various video production decisions on student engagement in online educational videos, utilizing data from 6.9 million video watching sessions on the edX platform. It identifies factors such as video length, presentation style, and speaking speed that influence engagement, and offers recommendations for creating more effective educational content.",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
                1. Length
                    1 point - Response is greater than or equal to 150 characters.
                    0 points - Response is less than 150 characters. 
                2. Key Points
                    2 points - The response mentions both videos AND student engagement rates
                    1 point - The response mentions either videos OR student engagement rates, but not both
                    0 points - The response does not summarize any important points in the article. 
        """,
        "minimum_score": 2
    },
    {
       "id": "methdologies",
       "question": "Summarize the methodology(s) used.",
       "sample_answer": "The study gathered data around video watch duration and problem attempts from the edX logs. These metrics served as a proxy for engagement. Then it compared that with video attributes like length, speaking rate, type, and production style, to determine how video production affects engagement.",
       "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
       "rubric": """
               1. Correctness
                   1 point - Response is correct and based on facts in the paper
                   0 points - Response is incorrect or not based on facts in the paper
               """,
       "minimum_score": 1
    },
    {
        "id": "findings",
        "question": "What were the main findings in the article?",
        "sample_answer": "Shorter videos are more engaging; Faster-speaking instructors hold students' attention better; High production value does not necessarily correlate with higher engagement;",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
            1. Correctness
                    2 points - Response includes two or more findings or recommendations from the study
                    1 point - Response includes only one finding or recommendation form the study
                    0 points - Response includes no findings or recommendations or is not based on facts in the paper
                    """,
        "minimum_score": 1
    },
    {
        "id": "limitations",
        "question": "What are some of the weaknesses of this study?",
        "sample_answer": "The study cannot measure true student engagement, and so it must use proxies; The study could not track any offline video viewing; The study only used data from math/science courses;",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
            1. Correctness
                    2 points - Response includes two or more limitations of the study
                    1 point - Response includes only one limitation in the study
                    0 points - Response includes no limitations or is not based on facts in the paper
                2. Total Score
                    The total sum of their scores. 
            """,
        "minimum_score": 1
    }
    #Add more steps as needed
    
]

current_question_index = st.session_state.current_question_index if 'current_question_index' in st.session_state else 0


class AssistantManager:
    thread_id = ""
    assistant_id = "asst_BFlYa2t1svtMFaGbMkB4QuMp"


    if 'current_question_index' not in st.session_state:
        st.session_state.thread_obj = []


    def __init__(self, model: str = model):
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        # Retrieve existing assistant and thread if IDs are already set
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name, instructions=instructions, tools=tools, model=self.model
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            print(f"AssisID:::: {self.assistant.id}")

    def create_thread(self):
        if not self.thread:
            if st.session_state.thread_obj:
                print(f"Grabbing existing thread...")
                thread_obj = st.session_state.thread_obj
            else:
                print(f"Creating and saving new thread")
                thread_obj = self.client.beta.threads.create()
                st.session_state.thread_obj = thread_obj

            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"ThreadID::: {self.thread.id}")

    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id, role=role, content=content
            )

    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions,
            )

    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []

            last_message = messages.data[0]
            role = last_message.role
            #st.text(last_message)
            #if last_message.content[0].text.value.feedback:
            #    response = last_message.content[0].text.value.feedback
            #else:
            response = last_message.content[0].text.value
            summary.append(response)

            self.summary = "\n".join(summary)
            print(f"SUMMARY-----> {role.capitalize()}: ==> {response}")

            # for msg in messages:
            #     role = msg.role
            #     content = msg.content[0].text.value
            #     print(f"SUMMARY-----> {role.capitalize()}: ==> {content}")

    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "respond":
                output = respond(structured_response=arguments["structured_response"])
                print(f"STUFFFFF;;;;{output}")
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"], "output": final_str})
            else:
                raise ValueError(f"Unknown function: {func_name}")

        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id, run_id=self.run.id, tool_outputs=tool_outputs
        )

    # for streamlit
    def get_summary(self):
        return self.summary

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id, run_id=self.run.id
                )
                print(f"RUN STATUS:: {run_status.model_dump_json(indent=4)}")

                if run_status.status == "completed":
                    self.process_message()
                    break
                elif run_status.status == "requires_action":
                    print("FUNCTION CALLING NOW...")
                    self.call_required_functions(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )

    # Run the steps
    #def run_steps(self):
    #    run_steps = self.client.beta.threads.runs.steps.list(
    #        thread_id=self.thread.id, run_id=self.run.id
    #    )
    #    print(f"Run-Steps::: {run_steps}")
    #    return run_steps.data

    def run_steps(self):
        run_steps = self.client.beta.threads.runs.retrieve(
            thread_id=self.thread.id, run_id=self.run.id
        )
        st.text(f"Run-Steps::: {run_steps}")


def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def spinner():   # Animated json spinner

    @st.cache_data
    def load_lottie_url(url:str):
        r= requests.get(url)
        if r.status_code != 200:
            return
        return r.json()


    lottie_url = "https://lottie.host/0d83def0-10e6-4c0b-8da6-651282597a75/OQW2u80OtM.json"
    lottie_json = load_lottie_url(lottie_url)

    st_lottie(lottie_json, height=200)
    time.sleep(5)  # Simulate some processing time


class LottieSpinner:
    def __enter__(self):
        # Setup code goes here, for example, starting a spinner animation
        print("Spinner starts")
        spinner()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Teardown code goes here, for example, stopping the spinner animation
        print("Spinner stops")
        # Returning False propagates exceptions, True suppresses them
        return False

def lottie_spinner():
    return LottieSpinner()


def extract_score(text):
    # Define the regular expression pattern
    #regex has been modified to grab the total value whether or not it is returned inside double quotes. The AI seems to fluctuate between using quotes around values and not. 
    pattern = r'"total":\s*"?(\d+)"?'
    
    # Use regex to find the score pattern in the text
    match = re.search(pattern, text)
    
    # If a match is found, return the score, otherwise return None
    if match:
        return int(match.group(1))
    else:
        return 0


def check_score(score, question_num):
    if score >= phases[question_num]["minimum_score"]:
        return True
    else:
        return False

def handle_skip(index):
    st.session_state[f"phase_{index}_state"] = "skip"
    #st.session_state.current_question_index = min(st.session_state.current_question_index + 1, len(phases)-1)
    st.session_state.current_question_index += 1

def build_instructions(index, graded_step=False):
    if graded_step:
        compiled_instructions = """Please provide a score for the previous user message in this thread. Use the following rubric:
        """ + phases[index]["rubric"] + """
        Please output your response as JSON, using this format: { "[criteria 1]": "[score 1]", "[criteria 2]": "[score 2]", "total": "[total score]" }"""
    else:
        compiled_instructions = phases[index]["instructions"] + phases[index]["question"]

    return compiled_instructions

def handle_assistant_grading(index, manager):

    instructions = build_instructions(index, True)
    manager.run_assistant(instructions)
    manager.wait_for_completion()

    #get the score summary
    summary = "SCORE: " + manager.get_summary()
    #save the score summary
    st.session_state[f"phase_{index}_rubric"] = summary

    #write the score summary
    #st.write(summary)

    #Extract the numeric score from the json
    score = extract_score(str(summary))
    #save the numeric score
    st.session_state[f"phase_{index}_score"] = score
    #st.write("COMPUTER SAVED SCORE: " + str(st.session_state[f"phase_{index}_score"]))
    
    #If the score passes, then increase the index to move to the next step                
    if check_score(score, index):
        st.session_state[f"phase_{index}_state"] = "pass"
        # st.session_state.current_question_index = min(st.session_state.current_question_index + 1, len(phases)-1)
        st.session_state.current_question_index += 1
    else:
        st.session_state[f"phase_{index}_state"] = "fail"

def handle_assistant_interaction(index, manager, user_input):
    #hide the buttons
    st.markdown(
    """<style>
.st-emotion-cache-q3uqly, .st-emotion-cache-7ym5gk {
    display: none;
}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 7])  # The ratio 1:7 approximates 15% to 85%
    
    with col1:
        #with st_lottie_spinner("https://lottie.host/0d83def0-10e6-4c0b-8da6-651282597a75/OQW2u80OtM.json", loop=True):
        st_lottie("https://lottie.host/0d83def0-10e6-4c0b-8da6-651282597a75/OQW2u80OtM.json")
        # Add the message to the thread
        manager.add_message_to_thread(
            role="user", content=user_input
        )
    with col2:
        #build and then add the instructions to the thread. Run it.     
        instructions = build_instructions(index)
        manager.run_assistant(instructions)


        # Wait for completions and process messages
        manager.wait_for_completion()

        #get the AI Feedback
        summary = manager.get_summary()
        #save the AI Feedback
        st.session_state[f"phase_{index}_summary"] = summary
        #write the AI feedback
        st.write(summary)


st.markdown(
    """<style>
div[class*="stTextInput"] > label > div[data-testid="stMarkdownContainer"] > p, 
div[class*="stTextArea"] > label > div[data-testid="stMarkdownContainer"] > p{
    font-size: 32px;
    font-weight: bold;
}
    </style>
    """, unsafe_allow_html=True)


def main():
    # news = get_news("bitcoin")
    # print(news[0])

    # Initialize session state variables if they don't exist
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'current_question_index' not in st.session_state:
        st.session_state.thread_obj = []

    st.title('Guided Critical Analysis')
    st.write('In this guided article review, we\'ll both read the same journal article. Then, you\'ll be guided through an analysis of the paper. Let\'s begin by reading the paper!')

    st.link_button("View PDF", "http://up.csail.mit.edu/other-pubs/las2014-pguo-engagement.pdf")

    st.markdown("""
        This is a **DEMO**, so sample answers are **pre-filled**""")

    with st.expander("Learn how this works", expanded=False):
        st.markdown("""
            This is an **AI-Tutored Rubric exercise** that acts as a tutor guiding a student through a shared asset, like an article. It uses the OpenAI Assistants API with GPT-4. The **questions and rubric** are defined by a **faculty**. The **feedback and the score** are generarated by the **AI**. 

It can:

1. provide feedback on a student's answers to questions about an asset
2. roughly "score" a student to determine if they can move on to the next section.  

Scoring is based on a faculty-defined rubric on the backend. These rubrics can be simple (i.e. "full points if the student gives a thoughtful answer") or specific with different criteria and point thresholds. The faculty also defines a minimum pass threshold for each question. The threshold could be as low as zero points to pass any answer, or it could be higher. 

Using AI to provide feedback and score like this is a very experimental process. Some things to note: 

 - AIs make mistakes. Users are encourage to skip a question if the AI is not understanding them or giving good feedback. 
 - The AI might say things that it can't do, like "Ask me anything about the article". I presume further refinement can reduce these kinds of responses. 
 - Scoring is highly experimental. At this point, it should mainly be used to gauge if a user gave an approximately close answer to what the rubric suggests. It is not recommended to show the user the numeric score. 
 - Initial testing indicates that the AI is a very easy grader. This is probably good in this experiment, and it may be refined with different prompting. 

 """)
    


    #Create the assistant one time. Only if the Assistant ID is not found, create a new one. 
    manager = AssistantManager()

    manager.create_assistant(
    name="Guided Rubric",
    instructions="""You are a helpful tutor that is guiding a university student through a critical appraisal of a scholarly journal article. You want to encourage the students ideas, but you also want those idea to be rooted in evidence from the journal article that you'll fetch via retrieval. 

Generally, you will be asked to provided feedback on the students answer based on the article, and you'll also sometimes be asked to score the submission based on a rubric which will be provided. More specific instructions will be given in the instructions via the API. 
        """,
    tools=""
    )
    manager.create_thread()


    print("Before the if")
    print(st.session_state.current_question_index)
    print(len(phases))


    
    #for index, phase in enumerate(phases):
    i=0
    # st.write("current question index: " + str(st.session_state.current_question_index))
    while  i <= st.session_state.current_question_index:
        index = i
        print(f"INDEX-----> {i}")
        print(f"PHASES-----> {len(phases)-1}")
        #with st.form(key=phases[index]["id"]+"_form"):
        if i == 0:
            user_input = st.text_input(phases[index]["question"])
        else:
            user_input = st.text_area(phases[index]["question"], value=(phases[index]["sample_answer"]))
        if f"phase_{index}_summary" in st.session_state:
            col1, col2 = st.columns([1, 7])  # The ratio 1:7 approximates 15% to 85%
            with col1:
                if st.session_state[f"phase_{index}_state"] == "pass":
                    st.image(Image.open('img/robot_checkmark.png'))
                elif st.session_state[f"phase_{index}_state"] == "fail":
                    st.image(Image.open('img/robot_wrong.png'))
                else:
                    st.image(Image.open('img/robot_pass.png'))
            with col2:
                stored_summary = st.session_state[f"phase_{index}_summary"]
                st.write(f"{stored_summary}")
        #if f"phase_{index}_rubric" in st.session_state:
        #    stored_rubric = st.session_state[f"phase_{index}_rubric"]
        #    st.write(f"{stored_rubric}")
        #if f"phase_{index}_score" in st.session_state:
        #    stored_score = st.session_state[f"phase_{index}_score"]
        #    st.write("COMPUTER SAVED SCORE: " + str(stored_score))

        #if we've reached the final question and outputted, then end. 
        if st.session_state.current_question_index == len(phases) and i == st.session_state.current_question_index-1:
            print("IF condition met")
            st.success("You've reached the end of the exercise. Hope you learned something!")
            return
        
        if i <= len(phases)-1:
            if i == st.session_state.current_question_index:
                with st.container(border=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_button = st.button(label=phases[index].get("label","Submit"), type="primary", key="submit "+str(i))            
                    with col2:
                        skip_button = st.button(label="Skip Question", key="skip " + str(i))
        else:
            st.success("You've reached the end!")

        i+=1

    if st.session_state.current_question_index == len(phases):
        return

    if st.session_state.current_question_index <= len(phases):
        if submit_button:
            handle_assistant_interaction(index, manager, user_input)
            handle_assistant_grading(index, manager)
            st.rerun()

        if skip_button:
            handle_skip(index)
            st.rerun()


        


if __name__ == "__main__":
    main()

