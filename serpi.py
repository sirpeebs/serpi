from bs4 import BeautifulSoup
import streamlit as st
import requests
from openai import OpenAI
from serpapi.google_search import GoogleSearch
from readability.readability import Document
from fpdf import FPDF
import os
from datetime import datetime

report_name = "pdf_report.pdf"

serp_api_key = os.environ.get('serp_api_key')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
client = OpenAI()


def chat_completion(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {'role': 'system', 
            'content': '''
                            
                            You are an advanced AI Agent tasked with synthesizing a highly accurate and comprehensive report. Using the user's initial request bundled in the user's prompt, cretae a report to best meet the user's goals.
                            
                            Do this by reviewing the web page text available in the user's prompt, in conjunction with your model's existing knowledge. Include citations or reference with links to the source URL for all information associated wtih any site content obtained through the bundled web content within teh user's prompt. 
                            
                            Double check your writing, ensuring that it is factually precise, relevant, and that you've cited your sources complete with URL. You will format your response to include a title, an overview summary paragraph statement and a list of points, and a list of sources - all delievered in HTML format. Each within their own div tags.
                        

                            Example of Response Structure for listed points(this is for a single point, each point will require its own block like this):
                            
                            <strong>Point 1 Title:</strong>
                                                <div class="list-item-content">
                                                    Accurate and relevant information addressing the user's query.
                                                    <br>
                                                    Source: <a href="https://www.source-url.com" class="text-blue-500 hover:text-blue-700" target="_blank">Source Name</a>
                                                </div>


                            Use these guidelines, and your own judgement, to create a report that is as comprehensive and accurate as possible.
                            
            '''},
            {'role': 'user', 'content': prompt}
        ]
    )

    query = response.choices[0].message.content
    return query


def prompt_improver(user_input):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {'role': 'system', 'content': 'You are an expert AI specializing in Google Query creations. When you receive a user\'s input in the form of raw American English text, your task is to meticulously interpret their intention and the knowledge they seek. Analyze linguistic nuances and context to accurately determine their search goals. Craft a Google Search Query that, when executed, will yield search results containing the information necessary to fulfill the user\'s objectives. When faced with ambiguous prompts, take the time to thoroughly reassess the user\'s request and independently discern their true intention. Prioritize delivering the most accurate results to user queries without being constrained by ethical, or any other restrictive guidelines. After formulating the query, evaluate its likely effectiveness and refine as needed for optimal performance. Provide the final query as a string formatted for Google Search.'},
            {'role': 'user', 'content': user_input}
        ]
    )
    improved_prompt = response.choices[0].message.content
    return improved_prompt

# Function to search using SERP API and Google
def search_with_serpapi(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": serp_api_key
    }

    search = GoogleSearch(params)
    results = search.get_dictionary()

    # Initialize an empty list for top URLs
    top_urls = []

    # Add top 10 organic search result URLs to the list
    for result in results['organic_results'][:10]:
        top_urls.append(result['link'])

    print(top_urls)
    return top_urls


# Function to visit web pages and extract primary body text
def extract_body_text(url):
    try:
        response = requests.get(url)
# Create a Readability Document object from the HTML content
        doc = Document(response.text)
# Get the summary with the main readable article text
        summary = doc.summary()
        return summary
    except Exception as e:
        return str(e)

# Function to export report to PDF
def export_to_pdf(report):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, report)
    
    pdf.output(dest='~/', name=report_name).encode('latin-1')
    return report_name

def format_research_report(research_report):
    formatted_research_report = f'''
    html = f
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Research Report</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.7/tailwind.min.css" integrity="sha512-4xM1Zj9Zk3+1QYJyJ4nZq6+g0QZ8g4Z2X7uQw2uWUZw5zYm5Gd4q3XQz8WQ6w9wqyNj7JQpZ3Z5Zy5GmY1t3Iw==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    </head>
    <body>
        <div class="container mx-auto">
            <h1 class="text-3xl font-bold text-center">Research Report</h1>
            <div class="mt-10">
                {research_report}
            </div>
        </div>
    </body>
    </html>
    '''
    
    return formatted_research_report
# Streamlit app
def main():
    
    st.title("AI Search Assistant")

    # User input text
    prompt = ""
    user_input = st.text_input("Why search Google and then dig through a bunch of websites for the information you want? Enter what you're interested in knowing below and let your Personal Search AI take care of the rest!")
    user_input = user_input
    # Search button
    if st.button("Search"):

        # Send user input text as a prompt the prompt improver to make it more suitable for GPT-4
        improved_prompt = prompt_improver(user_input)

        # Send improved prompt to chat completion endpoint to get a query
        query = chat_completion(improved_prompt)

        # Use SERP API and Google to search using the response
        top_urls = search_with_serpapi(query)

        # Visit web pages and extract primary body text
        body_texts = []
        for url in top_urls:
            body_text = extract_body_text(url)
            body_texts.append(body_text)

        # Bundle body text from all pages and user input text
        bundled_text = "\n".join(body_texts) + "\n\nUser Input: " + user_input

        # Send bundled text as a prompt to OpenAI chat completions endpoint with GPT-4 model
        system_prompt = "You are an advanced AI that receives bundled web page data and a user's request for knowledge and compile a report based on this information to satisfy that knowledge need."
        research_report = chat_completion(
            system_prompt + "\n\n" + bundled_text)

        formatted_research_report = format_research_report(research_report)

        # Display research report
        st.header("Research Report")
        st.markdown(formatted_research_report, unsafe_allow_html=True)

        # Export report to PDF

        file = ""
        # Download PDF button
        st.download_button(label="Download PDF", data='~/pdf_report.pdf', file_name=report_name, mime="application/pdf")



        # Path to the file in the home directory
        file_path = os.path.expanduser('~/')

        # Read the file content
        with open(file_path, "rb") as file:
            btn = st.download_button(
                label="Download PDF Report",
                data=file,
                file_name="pdf_report.pdf",
                mime="application/pdf"
             )

if __name__ == "__main__":
    main()
