import os
import openai
from serpapi import GoogleSearch
import streamlit as st
import re
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# Load Open AI API key from .env file
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Set Open AI API key
openai.api_key = openai_api_key

def get_company_info_openai(company_name):
    client = openai.ChatCompletion()
    response = client.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Get the CEO, industry, career opportunities, products, location, competitors, and email of {company_name}"}
        ]
    )
    return response.choices[0].message.content

def parse_openai_response(response):
    structured_response = {
        "Description": "N/A",
        "Website": "N/A",
        "CEO": "N/A",
        "Industry": "N/A",
        "Career": "N/A",
        "Products": "N/A",
        "Location": "N/A",
        "Competitors": "N/A",
        "Email": "N/A"
    }
    
    lines = response.split("\n")
    for line in lines:
        parts = line.split(": ")
        if len(parts) == 2:
            key = parts[0].strip().lower()
            value = parts[1].strip()
            if "description" in key:
                structured_response["Description"] = value
            elif "website" in key:
                structured_response["Website"] = value
            elif "ceo" in key:
                structured_response["CEO"] = value
            elif "industry" in key:
                structured_response["Industry"] = value
            elif "career" in key:
                structured_response["Career"] = value
            elif "products" in key:
                structured_response["Products"] = value
            elif "location" in key:
                structured_response["Location"] = value
            elif "competitors" in key:
                structured_response["Competitors"] = value
            elif "email" in key:
                structured_response["Email"] = value
    
    return structured_response

def get_company_info(company_name):
    params = {
        "q": company_name,
        "num": 1
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if 'organic_results' not in results or len(results['organic_results']) == 0:
        return {"Description": "", "Website": ""}
    
    result = results['organic_results'][0]
    description = result.get("snippet", "")
    website = result.get("link", "")
    if not website:
        website = result.get("title", "")
    
    response = {
        "Description": description,
        "Website": website
    }
    return response

def get_wikipedia_description(company_name):
    wikipedia_url = f"https://en.wikipedia.org/wiki/{company_name}"
    response = requests.get(wikipedia_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    description = ' '.join(paragraph.text for paragraph in paragraphs[:2]).strip()
    return description

# Create a Streamlit app
st.title("Company Information Extractor")

# Get company name from user input
company_name = st.text_input("Enter company name")

if st.button("Get Company Information"):
    if company_name:
        # Fetch the company information using SerpApi
        response = get_company_info(company_name)
        
        if "error" in response or response["Description"] == "" or response["Website"] == "":
            # Fetch the description and website using OpenAI API
            openai_response = get_company_info_openai(company_name)
            openai_structured_response = parse_openai_response(openai_response)
            response["Description"] = openai_structured_response["Description"]
            response["Website"] = openai_structured_response["Website"]
        
        if "error" in response:
            st.error(response["error"])
        else:
            # Parse the response to extract structured information
            structured_response = response
            
            # Use Open AI API to fetch additional details
            openai_response = get_company_info_openai(company_name)
            openai_structured_response = parse_openai_response(openai_response)
            
            # Update the structured response with Open AI API results
            structured_response["CEO"] = openai_structured_response["CEO"]
            structured_response["Industry"] = openai_structured_response["Industry"]
            structured_response["Career"] = openai_structured_response["Career"]
            structured_response["Products"] = openai_structured_response["Products"]
            structured_response["Location"] = openai_structured_response["Location"]
            structured_response["Competitors"] = openai_structured_response["Competitors"]
            structured_response["Email"] = openai_structured_response["Email"]
            
            # Fetch website description from Wikipedia
            wikipedia_description = get_wikipedia_description(company_name)
            structured_response["Description"] = wikipedia_description if wikipedia_description else structured_response["Description"]
            
            # Display the structured response
            st.subheader("Extracted Information")
            st.write(f"**Company Name:** {company_name}")
            st.write(f"**CEO:** {structured_response['CEO']}")
            st.write(f"**Industry:** {structured_response['Industry']}")
            st.write(f"**Career Opportunities:** {structured_response['Career']}")
            st.write(f"**Products:** {structured_response['Products']}")
            st.write(f"**Location:** {structured_response['Location']}")
            st.write(f"**Competitors:** {structured_response['Competitors']}")
            st.write(f"**Email:** {structured_response['Email']}")
    else:
        st.error("Please enter a company name.")
