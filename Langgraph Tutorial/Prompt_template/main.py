### This file demonstrates how to create a simple reflection and generation chain using LangChain. The reflection chain allows the model to critique its own responses and improve them based on user feedback, while the generation chain focuses on creating content based on user prompts. ###

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage 
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from Langgraph_Tutorial.Stateful_framework.Prompt_template.chain import generate_chain, reflection_chain
from langgraph.graph.message import MessageGraph
from typing_extensions import TypedDict
from typing import TypedDict, Annotated

class MessageGraph(TypedDict):
    messages:Annotated[list[BaseMessage], add_messages]

REFLECT = "reflect" 
GENERATE = "generate"

## Define the nodes for the generation and reflection chains. Each node takes the current state of the graph (which includes the messages) and returns a new state with updated messages based on the respective chain's output. ##
def generation_node(state:MessageGraph):
    return {"messages":[generate_chain.invoke({"messages":state["messages"]})]}

def reflection_node(state:MessageGraph):
    res = reflection_chain.invoke({"messages":state["messages"]})
    return {"messages": [HumanMessage(content = res.content)]}

## Build the state graph by adding the nodes and defining the edges between them. The graph will start with the generation node, and based on the user's feedback, it will either continue to reflect or end the process after a certain number of iterations. ##
builder = StateGraph(state_schema=MessageGraph)
builder.add_node(GENERATE, generation_node)
builder.add_node(REFLECT, reflection_node)
builder.set_entry_point(GENERATE)

def should_continue(state:MessageGraph):
    if len(state["messages"])> 6:
        return END
    return REFLECT

## Build conditional edges for the graph. After the generation node is executed, the graph will check if it should continue to the reflection node or end the process based on the number of messages in the state. ##
builder.add_conditional_edges(GENERATE,should_continue,{REFLECT: REFLECT,END: END})
graph = builder.compile()
print(graph.get_graph().draw_mermaid())
graph.get_graph().print_ascii()

if __name__ == "__main__":
    print("Hello LangGraph")
    inputs = {
        "messages": [
            HumanMessage(
                content="""Make this tweet better:"
                                    @LangChainAI
            — newly Tool Calling feature is seriously underrated.

            After a long wait, it's  here- making the implementation of agents across different models with function calling - super easy.

            Made a video covering their newest blog post

                                  """
            )
        ]
    }
    response = graph.invoke(inputs)
    print(response)
