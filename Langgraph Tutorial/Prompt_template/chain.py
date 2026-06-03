### This file demonstrates how to create a simple reflection and generation chain using LangChain. The reflection chain allows the model to critique its own responses and improve them based on user feedback, while the generation chain focuses on creating content based on user prompts. ###

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

## This is a simple example of a reflection chain. The user will provide an initial prompt, and the model will generate a response. The user can then provide feedback on the response, and the model will generate a revised response based on the feedback. ##
reflection_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a viral twitter influencer grading a tweet. Generate critique and recommendations for the user's tweet."
            "Always provide detailed recommendations, including requests for length, virality, style, etc.",
        ),
        MessagesPlaceholder(variable_name = "messages"),
    ]
)

## This is a simple example of a generation chain. The user will provide an initial prompt, and the model will generate a response. The user can then provide feedback on the response, and the model will generate a revised response based on the feedback. ##
generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a twitter techie influencer assistant tasked with writing excellent twitter posts."
            " Generate the best twitter post possible for the user's request."
            " If the user provides critique, respond with a revised version of your previous attempts.",
        ),
        MessagesPlaceholder(variable_name = "messages"),
    ]
)

## Initialize the language model and create the chains ##
llm = ChatOpenAI(api_key = "Keep_your_api_key_here")
generate_chain = generation_prompt | llm 
reflection_chain = reflection_prompt | llm