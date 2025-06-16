# openai-realtimeapi-tools
Function calling
The Realtime models also support function calling, which enables you to execute custom code to extend the capabilities of the model. Here's how it works at a high level:

When updating the session or creating a response, you can specify a list of available functions for the model to call.
If when processing input, the model determines it should make a function call, it will add items to the conversation representing arguments to a function call.
When the client detects conversation items that contain function call arguments, it will execute custom code using those arguments
When the custom code has been executed, the client will create new conversation items that contain the output of the function call, and ask the model to respond.
Let's see how this would work in practice by adding a callable function that will provide today's horoscope to users of the model. We'll show the shape of the client event objects that need to be sent, and what the server will emit in turn.

Configure callable functions
First, we must give the model a selection of functions it can call based on user input. Available functions can be configured either at the session level, or the individual response level.

Session: session.tools property in session.update
Response: response.tools property in response.create
Here's an example client event payload for a session.update that configures a horoscope generation function, that takes a single argument (the astrological sign for which the horoscope should be generated):

session.update
```
{
  "type": "session.update",
  "session": {
    "tools": [
      {
        "type": "function",
        "name": "generate_horoscope",
        "description": "Give today's horoscope for an astrological sign.",
        "parameters": {
          "type": "object",
          "properties": {
            "sign": {
              "type": "string",
              "description": "The sign for the horoscope.",
              "enum": [
                "Aries",
                "Taurus",
                "Gemini",
                "Cancer",
                "Leo",
                "Virgo",
                "Libra",
                "Scorpio",
                "Sagittarius",
                "Capricorn",
                "Aquarius",
                "Pisces"
              ]
            }
          },
          "required": ["sign"]
        }
      }
    ],
    "tool_choice": "auto",
  }
}
```
The description fields for the function and the parameters help the model choose whether or not to call the function, and what data to include in each parameter. If the model receives input that indicates the user wants their horoscope, it will call this function with a sign parameter.

Detect when the model wants to call a function
Based on inputs to the model, the model may decide to call a function in order to generate the best response. Let's say our application adds the following conversation item and attempts to generate a response:

conversation.item.create

```
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [
      {
        "type": "input_text",
        "text": "What is my horoscope? I am an aquarius."
      }
    ]
  }
}
```
Followed by a client event to generate a response:

response.create
```
{
  "type": "response.create"
}
```
Instead of immediately returning a text or audio response, the model will instead generate a response that contains the arguments that should be passed to a function in the developer's application. You can listen for realtime updates to function call arguments using the response.function_call_arguments.delta server event, but response.done will also have the complete data we need to call our function.

response.done
```
{
  "type": "response.done",
  "event_id": "event_AeqLA8iR6FK20L4XZs2P6",
  "response": {
    "object": "realtime.response",
    "id": "resp_AeqL8XwMUOri9OhcQJIu9",
    "status": "completed",
    "status_details": null,
    "output": [
      {
        "object": "realtime.item",
        "id": "item_AeqL8gmRWDn9bIsUM2T35",
        "type": "function_call",
        "status": "completed",
        "name": "generate_horoscope",
        "call_id": "call_sHlR7iaFwQ2YQOqm",
        "arguments": "{\"sign\":\"Aquarius\"}"
      }
    ],
    "usage": {
      "total_tokens": 541,
      "input_tokens": 521,
      "output_tokens": 20,
      "input_token_details": {
        "text_tokens": 292,
        "audio_tokens": 229,
        "cached_tokens": 0,
        "cached_tokens_details": { "text_tokens": 0, "audio_tokens": 0 }
      },
      "output_token_details": {
        "text_tokens": 20,
        "audio_tokens": 0
      }
    },
    "metadata": null
  }
}
```
In the JSON emitted by the server, we can detect that the model wants to call a custom function:

Property	Function calling purpose
response.output[0].type	When set to function_call, indicates this response contains arguments for a named function call.
response.output[0].name	The name of the configured function to call, in this case generate_horoscope
response.output[0].arguments	A JSON string containing arguments to the function. In our case, "{\"sign\":\"Aquarius\"}".
response.output[0].call_id	A system-generated ID for this function call - you will need this ID to pass a function call result back to the model.
Given this information, we can execute code in our application to generate the horoscope, and then provide that information back to the model so it can generate a response.

Provide the results of a function call to the model
Upon receiving a response from the model with arguments to a function call, your application can execute code that satisfies the function call. This could be anything you want, like talking to external APIs or accessing databases.

Once you are ready to give the model the results of your custom code, you can create a new conversation item containing the result via the conversation.item.create client event.

conversation.item.create
```
{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_sHlR7iaFwQ2YQOqm",
    "output": "{\"horoscope\": \"You will soon meet a new friend.\"}"
  }
}
```
The conversation item type is function_call_output
item.call_id is the same ID we got back in the response.done event above
item.output is a JSON string containing the results of our function call
Once we have added the conversation item containing our function call results, we again emit the response.create event from the client. This will trigger a model response using the data from the function call.

response.create

```
{
  "type": "response.create"
}
```
